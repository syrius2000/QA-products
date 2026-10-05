"""Contract v1.2の必須項目と状態整合性を標準ライブラリで検証する。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CONTRACT_VERSION = "1.2"
CASE_STATUSES = {
    "draft", "review-in-progress", "author-action-required",
    "author-response-submitted", "verification-in-progress",
    "adjudication-required", "ready-for-closure", "closed", "blocked",
    "deferred", "risk-accepted", "superseded", "cancelled",
}
NEXT_ACTIONS = {
    "collect-evidence", "author-response", "reviewer-verification",
    "adjudication", "owner-decision", "reopen", "none",
}
FINDING_STATUSES = {"open", "in-progress", "awaiting-author", "verification-required", "closed"}
TERMINAL_RESULTS = {"fixed-and-verified", "risk-accepted", "evidence-gap", "deferred", "not-reproducible"}


def validate_document(document: Any) -> list[str]:
    """Contract v1.2違反をすべて返す。空リストは検証合格を示す。"""
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["document must be an object"]

    required = {"contract_version", "case_id", "case_status", "next_action", "case_revision", "findings", "terminal_result"}
    missing = sorted(required - document.keys())
    errors.extend(f"missing required field: {key}" for key in missing)
    unknown = sorted(set(document) - required)
    errors.extend(f"unknown top-level field: {key}" for key in unknown)
    if errors:
        return errors

    if document["contract_version"] != CONTRACT_VERSION:
        errors.append("contract_version must be '1.2'")
    if not isinstance(document["case_id"], str) or not re.fullmatch(r"QA-[0-9]{4,}", document["case_id"]):
        errors.append("case_id must match QA-[0-9]{4,}")
    if document["case_status"] not in CASE_STATUSES:
        errors.append(f"invalid case_status: {document['case_status']!r}")
    if document["next_action"] not in NEXT_ACTIONS:
        errors.append(f"invalid next_action: {document['next_action']!r}")
    if not isinstance(document["case_revision"], int) or isinstance(document["case_revision"], bool) or document["case_revision"] < 0:
        errors.append("case_revision must be a non-negative integer")
    if not isinstance(document["findings"], list):
        errors.append("findings must be an array")
    else:
        errors.extend(_validate_finding(index, finding) for index, finding in enumerate(document["findings"]))
    terminal = document["terminal_result"]
    if terminal is not None and terminal not in TERMINAL_RESULTS:
        errors.append(f"invalid terminal_result: {terminal!r}")
    if document["case_status"] == "closed" and terminal is None:
        errors.append("closed case requires terminal_result")
    if document["case_status"] != "closed" and terminal is not None:
        errors.append("terminal_result is only allowed when case_status is closed")
    return [error for error in errors if error]


def _validate_finding(index: int, finding: Any) -> str:
    prefix = f"findings[{index}]"
    if not isinstance(finding, dict):
        return f"{prefix} must be an object"
    required = {"id", "severity", "finding_status"}
    missing = required - finding.keys()
    if missing:
        return f"{prefix} missing required field: {sorted(missing)[0]}"
    if not re.fullmatch(r"QA-[0-9]{4,}-F[0-9]+", str(finding["id"])):
        return f"{prefix}.id has invalid format"
    if finding["severity"] not in {"critical", "high", "medium", "low"}:
        return f"{prefix}.severity is invalid"
    if finding["finding_status"] not in FINDING_STATUSES:
        return f"{prefix}.finding_status is invalid"
    if "technical_status" in finding and finding["technical_status"] not in {
        "fixed-and-verified", "partially-fixed", "unverified", "failed"
    }:
        return f"{prefix}.technical_status is invalid"
    if "author_disposition" in finding and finding["author_disposition"] not in {
        "accepted", "rejected-with-evidence", "fix-submitted", "deferred",
        "risk-accepted", "not-applicable", None,
    }:
        return f"{prefix}.author_disposition is invalid"
    return ""


def load_and_validate(path: Path) -> list[str]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot read JSON: {error}"]
    return validate_document(document)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate a Contract v1.2 JSON document")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    problems = load_and_validate(args.path)
    if problems:
        for problem in problems:
            print(problem)
        raise SystemExit(1)
    print("Contract v1.2 is valid")
