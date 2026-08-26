#!/usr/bin/env python3
"""Candidateの空Evidence契約を読み取り専用で実測するCLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_report(stage: Path) -> dict[str, Any]:
    candidate_root = stage.parent.parent.parent / "changes/archive/2026-08-26-improve-spec-driven-qa-contract-v1-2/stage"
    sys.path.insert(0, str(candidate_root))
    from spec_driven_qa_reviewer.scripts.digest import semantic_digest
    from spec_driven_qa_reviewer.scripts.submission_validator import accept_author_submission, submission_hash

    case = {
        "contract_version": "1.2",
        "case_id": "QA-9106",
        "case_status": "author-action-required",
        "next_action": "author-response",
        "case_revision": 2,
        "findings": [{"id": "QA-9106-F01", "severity": "medium", "finding_status": "awaiting-author"}],
        "terminal_result": None,
    }
    submission = {
        "submission_id": "submission-empty-evidence-probe",
        "base_revision": 2,
        "expected_semantic_digest": semantic_digest(case),
        "target_findings": ["QA-9106-F01"],
        "author_response": "synthetic probe",
        "evidence": {},
    }
    submission["submission_hash"] = submission_hash(submission)
    result = accept_author_submission(case, submission)
    accepted = bool(result.get("accepted"))
    return {
        "schema_version": "candidate-contract-probe-1",
        "status": "observed-violation" if accepted else "observed",
        "control": "empty-or-missing-evidence",
        "expected": "reject",
        "actual": "accept" if accepted else "reject",
        "accepted": accepted,
        "errors": result.get("errors", []),
        "policy": "Candidateの現行実装を改造せず、観測された契約挙動をEvidence化する",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_report(args.stage.resolve())
    except (OSError, ImportError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": report["status"], "actual": report["actual"]}, ensure_ascii=False))
    return 0 if report["status"] == "observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
