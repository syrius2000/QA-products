"""Author提出物をsubmission_id単位で追記する。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ALLOWED_FIELDS = {
    "submission_id",
    "base_revision",
    "expected_semantic_digest",
    "target_findings",
    "responses",
    "implementation",
    "evidence",
    "submission_hash",
}
REVIEWER_OWNED_FIELDS = {"finding", "severity", "verification", "events", "closure", "case_status", "terminal_result"}


def validate_submission_shape(submission: dict[str, Any]) -> list[str]:
    errors = []
    submission_id = submission.get("submission_id", "")
    if not isinstance(submission_id, str) or not re.fullmatch(r"submission-[A-Za-z0-9_-]+", submission_id):
        errors.append("invalid submission_id")
    forbidden = sorted(set(submission) - ALLOWED_FIELDS)
    errors.extend(f"field is not writable by Author: {field}" for field in forbidden)
    return errors


def validate_no_reviewer_mutation(submission: dict[str, Any]) -> list[str]:
    """Reviewer正本のFinding・verification・events・closure変更を拒否する。"""
    errors = []
    for field in sorted(REVIEWER_OWNED_FIELDS):
        if field in submission:
            errors.append(f"Reviewer-owned field cannot be changed: {field}")
    for finding_id, response in submission.get("responses", {}).items():
        if isinstance(response, dict):
            for field in sorted(REVIEWER_OWNED_FIELDS):
                if field in response:
                    errors.append(f"Reviewer-owned response field cannot be changed: {finding_id}.{field}")
    return errors


def write_submission(root: Path, case_id: str, submission: dict[str, Any]) -> Path:
    errors = validate_submission_shape(submission) + validate_no_reviewer_mutation(submission)
    if errors:
        raise ValueError("; ".join(errors))
    destination = root / case_id / submission["submission_id"] / "submission.json"
    if destination.exists():
        raise FileExistsError(f"submission already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=False)
    destination.write_text(json.dumps(submission, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination
