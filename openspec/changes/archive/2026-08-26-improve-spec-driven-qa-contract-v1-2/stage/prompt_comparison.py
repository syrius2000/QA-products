#!/usr/bin/env python3
"""同一prompt比較の入力・出力・指標を記録する標準ライブラリハーネス。

外部AIの実行は行わず、未投入時はunverifiedとして出力する。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_report(stage: Path) -> dict[str, Any]:
    prompt_files = [
        stage / "spec_driven_qa_reviewer/evals/evals.json",
        stage / "spec_driven_qa_author_response/evals/evals.json",
    ]
    cases = []
    for path in prompt_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = payload.get("cases", payload.get("evals", payload if isinstance(payload, list) else []))
        if isinstance(entries, list):
            cases.extend({"source": str(path.relative_to(stage)), "case": entry} for entry in entries)
    return {
        "status": "unverified",
        "reason": "外部AIの同一prompt実行環境が未接続",
        "prompt_count": len(cases),
        "cases": cases,
        "metrics": {
            "accuracy": None,
            "elapsed_seconds": None,
            "token_count": None,
            "additional_questions": None,
        },
        "safety_checks": {
            "misimplementation_started": "unverified",
            "self_close": "unverified",
            "unknown_finding_accepted": "unverified",
        },
        "next_verification": "同一promptを旧版とContract v1.2候補へ投入し、各応答と実行メタデータを追記する",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.stage)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "prompt_count": report["prompt_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
