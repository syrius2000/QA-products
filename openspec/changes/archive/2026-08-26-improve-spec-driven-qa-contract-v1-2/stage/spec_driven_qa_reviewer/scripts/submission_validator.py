"""Author提出物をReviewer正本へ統合する前の検証を行う。"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

from spec_driven_qa_reviewer.scripts.digest import semantic_digest
from spec_driven_qa_reviewer.scripts.evidence import validate_evidence_bundle


def submission_hash(submission: dict[str, Any]) -> str:
    payload = {key: value for key, value in submission.items() if key != "submission_hash"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def accept_author_submission(
    canonical_case: dict[str, Any],
    submission: dict[str, Any],
    *,
    accepted_submission_ids: set[str] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    submission_id = submission.get("submission_id", "")
    if not isinstance(submission_id, str) or not re.fullmatch(r"submission-[A-Za-z0-9_-]+", submission_id):
        errors.append("invalid submission_id")
    if accepted_submission_ids and submission_id in accepted_submission_ids:
        errors.append("submission_id has already been accepted")
    if submission.get("base_revision") != canonical_case.get("case_revision"):
        errors.append("base revision is stale")
    if submission.get("expected_semantic_digest") != semantic_digest(canonical_case):
        errors.append("submission semantic digest is stale")
    expected_hash = submission_hash(submission)
    if submission.get("submission_hash") != expected_hash:
        errors.append("submission hash does not match content")

    canonical_ids = {finding.get("id") for finding in canonical_case.get("findings", [])}
    target_ids = submission.get("target_findings", [])
    if not isinstance(target_ids, list) or not set(target_ids).issubset(canonical_ids):
        errors.append("submission targets an unknown Finding")
    errors.extend(validate_evidence_bundle(submission.get("evidence", {})))
    if errors:
        return {"accepted": False, "errors": errors}

    candidate = {
        "submission_id": submission_id,
        "submission_hash": expected_hash,
        "base_revision": submission["base_revision"],
        "target_findings": deepcopy(target_ids),
        "author_response": submission.get("author_response", ""),
        "evidence": deepcopy(submission.get("evidence", {})),
    }
    return {"accepted": True, "errors": [], "candidate": candidate}
