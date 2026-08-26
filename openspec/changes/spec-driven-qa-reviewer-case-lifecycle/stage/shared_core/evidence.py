"""Evidence状態の技術判定とOwner判断の分離。"""

STATUSES = frozenset({"verified", "unverified", "evidence-gap", "risk-accepted", "fixed-and-verified"})


def status_is_valid(status: str) -> bool:
    return status in STATUSES


def can_mark_fixed_and_verified(status: str, owner_decision: bool = False) -> bool:
    return status == "verified" or (status == "risk-accepted" and owner_decision)
