#!/usr/bin/env python3
"""三版Bundleの同一性と安全な読み取り境界を検証する標準ライブラリCLI。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}


def repository_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "AGENTS.md").is_file() or (parent / "openspec").is_dir():
            return parent
    raise RuntimeError("repository root could not be resolved")


def load_config() -> tuple[Path, dict[str, Any]]:
    config_path = Path(__file__).with_name("bundles.json")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config.get("schema_version") != "parity-bundles-1":
        raise ValueError("unsupported bundle configuration")
    return config_path, config


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def included(relative: str) -> bool:
    path = Path(relative)
    return bool(relative) and not any(part in EXCLUDED_PARTS for part in path.parts) and path.suffix != ".pyc"


def directory_records(root: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not included(relative.as_posix()):
            continue
        if path.is_symlink():
            raise ValueError(f"symlink is not allowed: {relative}")
        if not path.is_file():
            continue
        data = path.read_bytes()
        records.append({"path": relative.as_posix(), "bytes": len(data), "sha256": sha256(data)})
    return records


def zip_records(path: Path) -> list[dict[str, Any]]:
    records = []
    with zipfile.ZipFile(path) as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename):
            name = info.filename.rstrip("/")
            if not name or not included(name):
                continue
            if info.is_dir():
                continue
            # Reject Unix symlink entries rather than extracting or following them.
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError(f"symlink is not allowed in archive: {name}")
            data = archive.read(info)
            records.append({"path": name, "bytes": len(data), "sha256": sha256(data)})
    return records


def resolve_source(config_path: Path, source: str) -> Path:
    # Source paths are repository-relative, even though the config is nested.
    root = repository_root()
    candidate = (root / source.removeprefix("../../../../")).resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"bundle source does not exist: {source}")
    return candidate


def inspect_bundle(name: str, entry: dict[str, Any], config_path: Path) -> dict[str, Any]:
    source = resolve_source(config_path, entry["source"])
    kind = entry.get("kind")
    if kind == "directory":
        if not source.is_dir():
            raise ValueError(f"directory bundle is not a directory: {source}")
        records = directory_records(source)
        source_digest = sha256("\n".join(f"{r['path']}:{r['sha256']}" for r in records).encode())
    elif kind == "zip":
        if not zipfile.is_zipfile(source):
            raise ValueError(f"zip bundle is not a zip file: {source}")
        records = zip_records(source)
        source_digest = sha256(source.read_bytes())
    else:
        raise ValueError(f"unsupported bundle kind: {kind}")
    if not records:
        raise ValueError(f"bundle is empty: {name}")
    return {
        "name": name,
        "version": entry["version"],
        "kind": kind,
        "source": str(source.relative_to(repository_root())),
        "source_sha256": source_digest,
        "roles": entry.get("roles", []),
        "file_count": len(records),
        "files": records,
    }


def build_manifest() -> dict[str, Any]:
    config_path, config = load_config()
    bundles = [inspect_bundle(name, entry, config_path) for name, entry in sorted(config["bundles"].items())]
    return {"schema_version": "parity-manifest-1", "bundles": bundles}


def validate_saved_manifest(path: Path, bundle_name: str | None = None) -> dict[str, Any]:
    expected = json.loads(path.read_text(encoding="utf-8"))
    actual = build_manifest()
    if expected != actual:
        raise ValueError("manifest mismatch: bundle contents changed")
    if bundle_name is not None and bundle_name not in {item["name"] for item in actual["bundles"]}:
        raise ValueError(f"unknown bundle: {bundle_name}")
    return actual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Manifestの保存先。省略時は標準出力")
    parser.add_argument("--bundle", choices=("legacy", "candidate", "compact"), help="表示対象Bundle")
    parser.add_argument("--verify-manifest", type=Path, help="保存済みManifestとの一致を検証")
    args = parser.parse_args(argv)
    try:
        manifest = build_manifest()
        if args.verify_manifest:
            manifest = validate_saved_manifest(args.verify_manifest, args.bundle)
        if args.bundle:
            manifest = {
                "schema_version": manifest["schema_version"],
                "bundles": [item for item in manifest["bundles"] if item["name"] == args.bundle],
            }
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
