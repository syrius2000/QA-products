"""QAケースの最小状態遷移。"""

TRANSITIONS = {
    "open": {"review", "handoff"},
    "needs-response": {"respond", "submit"},
    "verification-in-progress": {"verify", "close"},
    "closed": set(),
    "blocked": {"review", "respond"},
}


def can_transition(current: str, operation: str) -> bool:
    return operation in TRANSITIONS.get(current, set())
