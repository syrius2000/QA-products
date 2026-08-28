from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import QualityLoop
from .errors import QualityLoopError


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise QualityLoopError(
            "invalid-cli-arguments",
            message,
            remediation="--helpで引数を確認してください。",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description="人間中心の最小QMS協働ループ")
    parser.add_argument("--case-root", type=Path, default=Path("qms-cases"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-case")
    create.add_argument("--input", required=True)

    for command in ("review", "submit-response", "verify", "adjudicate"):
        operation = subparsers.add_parser(command)
        operation.add_argument("--case-id", required=True)
        operation.add_argument("--input", required=True)

    status = subparsers.add_parser("status")
    status.add_argument("--case-id", required=True)
    status.add_argument("--resume-format", choices=("markdown",))
    return parser


def read_payload(path_text: str) -> dict:
    try:
        if path_text == "-":
            payload = json.load(sys.stdin)
        else:
            with Path(path_text).open(encoding="utf-8") as handle:
                payload = json.load(handle)
    except FileNotFoundError as exc:
        raise QualityLoopError(
            "input-not-found",
            f"入力ファイルが見つかりません: {path_text}",
            exit_code=3,
            remediation="入力ファイルのパスを確認してください。",
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise QualityLoopError(
            "input-unreadable",
            "入力JSONを読み取れません。",
            exit_code=3,
            remediation="ファイル権限とJSON構文を確認してください。",
        ) from exc
    if not isinstance(payload, dict):
        raise QualityLoopError("invalid-input", "入力JSONはobjectで指定してください。")
    return payload


def run(argv: list[str] | None = None) -> int:
    case_id: str | None = None
    try:
        args = build_parser().parse_args(argv)
        loop = QualityLoop(args.case_root)
        case_id = getattr(args, "case_id", None)
        if args.command == "create-case":
            result = loop.create_case(read_payload(args.input))
        elif args.command == "review":
            result = loop.review(case_id, read_payload(args.input))
        elif args.command == "submit-response":
            result = loop.submit_response(case_id, read_payload(args.input))
        elif args.command == "verify":
            result = loop.verify(case_id, read_payload(args.input))
        elif args.command == "adjudicate":
            result = loop.adjudicate(case_id, read_payload(args.input))
        else:
            result = loop.status(case_id, resume_format=args.resume_format)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except QualityLoopError as exc:
        print(json.dumps(exc.as_result(case_id), ensure_ascii=False, indent=2))
        return exc.exit_code
    except Exception:
        result = {
            "status": "error",
            "error_code": "internal-error",
            "message": "予期しない内部エラーが発生しました。",
            "remediation": "入力を保存し、実装者へ調査を依頼してください。",
            "case_id": case_id,
            "case_revision": None,
            "state_changed": False,
            "next_role": None,
            "next_action": None,
            "handoff": None,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 4


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
