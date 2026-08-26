"""ケース直下の最小状態からworkflow phaseとterminal resultを導出する。"""

from __future__ import annotations

from typing import Any


NEXT_ACTION_BY_STATUS = {
    "draft": "collect-evidence",
    "review-in-progress": "collect-evidence",
    "author-action-required": "author-response",
    "author-response-submitted": "reviewer-verification",
    "verification-in-progress": "reviewer-verification",
    "adjudication-required": "adjudication",
    "ready-for-closure": "owner-decision",
    "closed": "none",
    "blocked": "reopen",
    "deferred": "owner-decision",
    "risk-accepted": "owner-decision",
    "superseded": "none",
    "cancelled": "none",
}


def derive_workflow_phase(case: dict[str, Any]) -> str:
    status = case.get("case_status")
    if status in {"closed", "superseded", "cancelled"}:
        return "terminal"
    if status in {"author-action-required", "author-response-submitted"}:
        return "author-response"
    if status in {"verification-in-progress", "ready-for-closure"}:
        return "verification"
    if status == "adjudication-required":
        return "adjudication"
    if status == "blocked":
        return "blocked"
    return "review"


def derive_terminal_result(case: dict[str, Any]) -> str | None:
    if case.get("case_status") != "closed":
        return None
    return case.get("terminal_result")


def validate_state(case: dict[str, Any]) -> list[str]:
    """永続化状態の許可された組合せだけを受理する。"""
    errors: list[str] = []
    status = case.get("case_status")
    next_action = case.get("next_action")
    if status not in NEXT_ACTION_BY_STATUS:
        return [f"unknown case_status: {status!r}"]
    expected_action = NEXT_ACTION_BY_STATUS[status]
    if next_action != expected_action:
        errors.append(f"next_action {next_action!r} is invalid for case_status {status!r}")
    if "workflow_phase" in case:
        errors.append("workflow_phase must be derived, not persisted")
    if status == "closed" and case.get("terminal_result") not in {
        "fixed-and-verified", "risk-accepted", "evidence-gap", "deferred", "not-reproducible"
    }:
        errors.append("closed case requires a valid terminal_result")
    if status != "closed" and case.get("terminal_result") is not None:
        errors.append("terminal_result is only valid for closed cases")
    return errors
