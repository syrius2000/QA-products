"""QA profileごとのreview cycle上限とエスカレーションを管理する。"""

from __future__ import annotations


MAX_CYCLES = {"lite": 1, "standard": 2, "strict": 3}


def cycle_limit(profile: str) -> int:
    if profile not in MAX_CYCLES:
        raise ValueError(f"unknown qa profile: {profile}")
    return MAX_CYCLES[profile]


def evaluate_cycle(profile: str, current_cycle: int) -> dict[str, object]:
    limit = cycle_limit(profile)
    if current_cycle >= limit:
        return {
            "status": "escalate",
            "next_action": "owner-decision",
            "auto_close": False,
            "cycle_limit": limit,
        }
    return {
        "status": "continue",
        "next_action": "reviewer-verification",
        "auto_close": False,
        "cycle_limit": limit,
    }
