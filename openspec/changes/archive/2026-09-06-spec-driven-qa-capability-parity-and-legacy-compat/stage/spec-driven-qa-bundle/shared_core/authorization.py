"""役割ごとの操作許可を公開する。"""

REVIEWER_OPERATIONS = frozenset({"review", "handoff", "verify", "close"})
AUTHOR_OPERATIONS = frozenset({"respond", "submit"})


def allowed(role: str, operation: str) -> bool:
    return operation in {"reviewer": REVIEWER_OPERATIONS, "author": AUTHOR_OPERATIONS}.get(role, ())
