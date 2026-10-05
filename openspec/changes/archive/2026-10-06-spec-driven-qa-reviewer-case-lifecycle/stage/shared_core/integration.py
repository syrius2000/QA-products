"""Author提出をReviewer統合前に検証する候補生成器。"""

from typing import Any

from .digest import content_digest


def verify_submission(handoff: dict[str, Any], submission: dict[str, Any]) -> list[str]:
    errors = []
    if submission.get("base_revision") != handoff.get("case_revision"):
        errors.append("base_revision_mismatch")
    if submission.get("expected_semantic_digest") != handoff.get("semantic_digest"):
        errors.append("semantic_digest_mismatch")
    allowed = set(handoff.get("finding_ids", []))
    targets = submission.get("target_findings", [])
    if not isinstance(targets, list) or not set(targets).issubset(allowed):
        errors.append("unknown_finding")
    responses = submission.get("responses", {})
    if not isinstance(responses, dict) or not set(targets).issubset(responses):
        errors.append("finding_response_missing")
    if not submission.get("evidence"):
        errors.append("evidence_missing")
    return errors


def verified_candidate(handoff: dict[str, Any], submission: dict[str, Any]) -> dict[str, Any]:
    errors = verify_submission(handoff, submission)
    if errors:
        raise ValueError("submission_rejected:" + ",".join(errors))
    return {"base_revision": handoff["case_revision"], "target_findings": submission["target_findings"], "submission_digest": content_digest(submission), "candidate": submission}
