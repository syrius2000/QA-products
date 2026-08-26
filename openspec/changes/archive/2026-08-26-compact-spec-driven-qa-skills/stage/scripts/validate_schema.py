"""正本Schemaの最小契約検証を行う標準ライブラリCLI。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent / "spec-driven-qa-bundle"
sys.path.insert(0, str(ROOT))
from shared_core.contract import validate_contract  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    value = json.loads(args.input.read_text(encoding="utf-8"))
    errors = validate_contract(value)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
