"""Author側の実行許可式とFast Path適格条件を検証する。"""

from __future__ import annotations

from typing import Any


def eligible_fast_path(change: dict[str, Any]) -> bool:
    return (
        change.get("severity") == "low"
        and change.get("local") is True
        and change.get("reversible") is True
        and change.get("destructive") is False
        and change.get("external_operation") is False
        and change.get("preapproved") is True
        and (change.get("documentation_only") is True or change.get("scoped") is True)
    )


def can_execute(
    *,
    repository_policy_allows: bool,
    user_authorization_covers_scope: bool,
    handoff_permission: bool,
    change: dict[str, Any],
) -> bool:
    return (
        repository_policy_allows
        and user_authorization_covers_scope
        and (handoff_permission or eligible_fast_path(change))
    )
