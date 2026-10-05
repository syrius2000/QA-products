#!/usr/bin/env python3
"""Author stageの配布対象を決定論的に計測する。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def measure(root: Path) -> dict:
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.parts[-1].endswith(".pyc") or "tests" in path.parts:
            continue
        data = path.read_bytes()
        files.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": len(data),
            "lines": data.count(b"\n"),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    return {
        "root": str(root),
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "total_lines": sum(item["lines"] for item in files),
        "files": files,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(measure(args.root), ensure_ascii=False, indent=2, sort_keys=True))
