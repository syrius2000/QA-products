"""技術未解決ケースの終了記録と再レビュー条件を検証する。"""

from __future__ import annotations

from typing import Any


NON_TECHNICAL_RESULTS = {"risk-accepted", "evidence-gap", "deferred", "not-reproducible"}
REQUIRED_FIELDS = {
    "owner",
    "rationale",
    "scope_or_assumptions",
    "compensating_controls",
    "expiry_or_review_trigger",
}


def validate_terminal_record(result: str, record: Any) -> list[str]:
    if result not in NON_TECHNICAL_RESULTS:
        return []
    if not isinstance(record, dict):
        return ["non-technical terminal result requires an owner record"]
    errors = []
    for key in sorted(REQUIRED_FIELDS):
        value = record.get(key)
        if key == "compensating_controls":
            if not isinstance(value, list) or not value:
                errors.append(f"terminal record requires non-empty list: {key}")
        elif not isinstance(value, str) or not value.strip():
            errors.append(f"terminal record requires non-empty value: {key}")
    return errors


def is_technical_completion(result: str) -> bool:
    return result == "fixed-and-verified"
