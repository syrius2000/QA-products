"""Bundle内ファイルの決定論的Manifestを生成する。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> None:
    bundle = Path(__file__).resolve().parent.parent / "spec-driven-qa-bundle"
    excluded = {"MANIFEST.json", "__pycache__"}
    files = []
    for path in sorted(bundle.rglob("*")):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        files.append({"path": str(path.relative_to(bundle)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (bundle / "MANIFEST.json").write_text(json.dumps({"version": 1, "files": files}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
