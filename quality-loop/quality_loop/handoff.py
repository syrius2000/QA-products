from __future__ import annotations

from uuid import uuid4


def issue_handoff(
    *,
    revision: int,
    next_role: str,
    next_action: str,
    purpose: str,
    inputs: list[str],
    open_items: list[str],
    expected_outputs: list[str],
) -> dict:
    return {
        "handoff_id": f"handoff-{uuid4()}",
        "issued_revision": revision,
        "next_role": next_role,
        "next_action": next_action,
        "purpose": purpose,
        "inputs": inputs,
        "open_items": open_items,
        "expected_outputs": expected_outputs,
        "status": "issued",
    }


def terminal_handoff(*, revision: int, result: str) -> dict:
    return {
        "handoff_id": f"handoff-{uuid4()}",
        "issued_revision": revision,
        "next_role": None,
        "next_action": None,
        "purpose": "Owner裁定により案件を終了する",
        "inputs": ["Reviewer検証", "Owner裁定"],
        "open_items": [],
        "expected_outputs": [],
        "status": "terminal",
        "terminal_result": result,
    }
