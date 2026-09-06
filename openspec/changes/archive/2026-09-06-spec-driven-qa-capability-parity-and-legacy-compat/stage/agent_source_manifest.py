#!/usr/bin/env python3
"""外部Agent／Run Evidenceの保存場所と内容ハッシュを固定するCLI。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import agent_aggregator


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_root(path: Path) -> Path:
    for parent in (path.resolve(), *path.resolve().parents):
        if (parent / "AGENTS.md").is_file() or (parent / "openspec").is_dir():
            return parent
    # テスト用の一時ディレクトリなど、リポジトリ外では絶対パスの基点を使う。
    return Path(path.resolve().anchor)


def display_root(path: Path) -> str:
    root = repository_root(path)
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path.resolve())


def build_manifest(agents_root: Path) -> dict[str, Any]:
    agents_root = agents_root.resolve()
    runs = agent_aggregator.discover_runs(agents_root)
    if not runs:
        raise ValueError("no Agent/Run manifests found")
    entries = []
    for agent_dir, run_dir, results_path in runs:
        files = []
        for path in sorted(item for item in run_dir.rglob("*") if item.is_file()):
            data = path.read_bytes()
            if agent_aggregator.contains_secret(data.decode("utf-8", errors="ignore")):
                raise ValueError("secret detected in source Evidence; source manifest was not written")
            files.append({
                "path": path.relative_to(run_dir).as_posix(),
                "bytes": len(data),
                "sha256": sha256(path),
            })
        entries.append({
            "agent_id": agent_dir.name,
            "run_id": run_dir.name,
            "source_dir": run_dir.relative_to(agents_root).as_posix(),
            "files": files,
        })
    return {
        "schema_version": "agent-source-manifest-1",
        "status": "observed",
        "source_root": display_root(agents_root),
        "retention_policy": "元Agent／Run Evidenceはアーカイブ側で不変保持し、現Changeには識別子とSHA-256だけを固定する",
        "agent_runs": entries,
    }


def verify_manifest(path: Path) -> Path:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "agent-source-manifest-1":
        raise ValueError("unsupported Agent source manifest")
    root = repository_root(path) / manifest["source_root"]
    if not root.is_dir():
        raise ValueError("Agent source root does not exist")
    for entry in manifest.get("agent_runs", []):
        run_dir = root / entry["source_dir"]
        if not run_dir.is_dir() or run_dir.parent.name != entry["agent_id"] or run_dir.name != entry["run_id"]:
            raise ValueError("Agent/Run source identity mismatch")
        actual_files = {path.relative_to(run_dir).as_posix() for path in run_dir.rglob("*") if path.is_file()}
        expected_files = {file_entry["path"] for file_entry in entry.get("files", [])}
        if actual_files != expected_files:
            raise ValueError("source Evidence file set changed")
        for file_entry in entry.get("files", []):
            file_path = run_dir / file_entry["path"]
            data = file_path.read_bytes() if file_path.is_file() else b""
            if agent_aggregator.contains_secret(data.decode("utf-8", errors="ignore")):
                raise ValueError("secret detected while verifying source Evidence")
            if not file_path.is_file() or file_path.stat().st_size != file_entry["bytes"] or sha256(file_path) != file_entry["sha256"]:
                raise ValueError(f"source Evidence hash mismatch: {file_entry['path']}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.verify:
            root = verify_manifest(args.verify.resolve())
            print(json.dumps({"ok": True, "status": "observed", "source_root": str(root)}, ensure_ascii=False))
            return 0
        if not args.agents_root or not args.output:
            raise ValueError("--agents-root and --output are required when creating a manifest")
        report = build_manifest(args.agents_root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "status": report["status"], "run_count": len(report["agent_runs"])}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
