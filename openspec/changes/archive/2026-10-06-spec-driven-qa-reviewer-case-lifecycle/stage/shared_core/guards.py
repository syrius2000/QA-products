"""正本変更前にhandoffの鮮度・改ざん・状態を検証する。"""

from typing import Any

from .digest import content_digest


def validate_handoff(handoff: dict[str, Any], current: dict[str, Any]) -> list[str]:
    errors = []
    if handoff.get("case_revision") != current.get("case_revision"):
        errors.append("revision_conflict")
    if handoff.get("expected_semantic_digest") != current.get("semantic_digest"):
        errors.append("semantic_digest_stale_or_tampered")
    if handoff.get("expected_content_digest") != current.get("content_digest"):
        errors.append("content_digest_stale_or_tampered")
    if current.get("case_status") not in {"needs-response", "verification-in-progress"}:
        errors.append("state_not_accepting_submission")
    return errors


def content_digest_for_case(case: dict[str, Any]) -> str:
    return content_digest({key: case[key] for key in sorted(case) if key not in {"content_digest", "semantic_digest"}})
