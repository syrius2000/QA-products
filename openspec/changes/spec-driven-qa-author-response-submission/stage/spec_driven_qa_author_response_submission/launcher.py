"""Author専用CLI。書込みは許可された提出ファイルだけに限定する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .shared_core_adapter import load_shared_core
from .submission import validate_and_save, validate_submission


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an Author submission")
    parser.add_argument("handoff", type=Path)
    parser.add_argument("submission", type=Path, help="JSON submission")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--case-dir", type=Path, help="QA case directory containing findings.yaml")
    parser.add_argument("--cycle", type=int, default=1)
    parser.add_argument("--save", action="store_true", help="検証成功後にAuthor提出先へ保存する")
    args = parser.parse_args(argv)
    try:
        load_shared_core()
        handoff = args.handoff.read_text(encoding="utf-8")
        submission = json.loads(args.submission.read_text(encoding="utf-8"))
        case_dir = args.case_dir or args.handoff.parent
        errors = validate_submission(submission, handoff, args.workspace, case_dir)
        if args.save and not errors:
            response_path, submission_path = validate_and_save(case_dir, args.handoff, submission, args.cycle, args.workspace)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "rejected", "error": str(exc)}, ensure_ascii=False))
        return 2
    if errors:
        print(json.dumps({"status": "rejected", "errors": errors}, ensure_ascii=False))
        return 2
    result = {"status": "awaiting-reviewer-verification", "submission_id": submission.get("submission_id")}
    if args.save:
        result["saved"] = [str(response_path), str(submission_path)]
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
