"""旧CLI相当のJSON入口。外部依存なし、未知majorは安全停止する。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "spec-driven-qa-bundle"
sys.path.insert(0, str(ROOT))
from shared_core.compat import invoke_legacy  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("reviewer", "author"))
    parser.add_argument("operation")
    parser.add_argument("--json", dest="payload", default="{}")
    args = parser.parse_args()
    try:
        result = invoke_legacy(args.role, args.operation, json.loads(args.payload))
    except (ValueError, json.JSONDecodeError):
        print(json.dumps({"status": "error", "code": "unknown_contract_major"}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
