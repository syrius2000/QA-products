#!/usr/bin/env python3
"""Manifest対象のSkill配布物を決定論的に計測する。標準ライブラリのみ。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

DEFAULT_EXCLUDED_PARTS = {"__pycache__", ".pytest_cache"}


def iter_files(root: Path, manifest: Path | None) -> list[Path]:
    if manifest is None:
        candidates = root.rglob("*")
    else:
        candidates = []
        for raw in manifest.read_text(encoding="utf-8").splitlines():
            relative = raw.strip()
            if not relative or relative.startswith("#"):
                continue
            candidates.append(root / relative)
    files = []
    for path in candidates:
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in DEFAULT_EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix == ".pyc":
            continue
        files.append(path)
    return sorted(set(files), key=lambda item: item.relative_to(root).as_posix())


def line_count(data: bytes) -> int:
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def category(relative: Path) -> str:
    return relative.parts[0] if len(relative.parts) > 1 else "root"


def measure(root: Path, manifest: Path | None = None) -> dict:
    root = root.resolve()
    files = iter_files(root, manifest.resolve() if manifest else None)
    records = []
    category_totals: dict[str, dict[str, int]] = {}
    for path in files:
        relative = path.relative_to(root)
        data = path.read_bytes()
        group = category(relative)
        record = {
            "path": relative.as_posix(),
            "bytes": len(data),
            "lines": line_count(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        records.append(record)
        totals = category_totals.setdefault(group, {"files": 0, "bytes": 0, "lines": 0})
        totals["files"] += 1
        totals["bytes"] += len(data)
        totals["lines"] += record["lines"]
    resident = [record["path"] for record in records if Path(record["path"]).name == "SKILL.md"]
    return {
        "schema_version": "size-metrics-1",
        "root": str(root),
        "manifest": str(manifest.resolve()) if manifest else None,
        "exclusions": ["__pycache__", ".pytest_cache", "*.pyc"],
        "counts": {
            "files": len(records),
            "bytes": sum(item["bytes"] for item in records),
            "lines": sum(item["lines"] for item in records),
        },
        "categories": dict(sorted(category_totals.items())),
        "resident_files": resident,
        "files": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = measure(args.root, args.manifest)
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
