"""Reviewer 正本書込み allowlist および 権限境界ガード。"""

import re
from pathlib import Path
from typing import Literal

REVIEWER_WRITABLE_PATTERNS = [
    re.compile(r"(^|/)QA-[^/]+/review\.md$"),
    re.compile(r"(^|/)QA-[^/]+/findings\.yaml$"),
    re.compile(r"(^|/)QA-[^/]+/traceability\.yaml$"),
    re.compile(r"(^|/)QA-[^/]+/events\.jsonl$"),
    re.compile(r"(^|/)QA-[^/]+/handoff\.md$"),
    re.compile(r"(^|/)QA-[^/]+/cycles/cycle-[0-9]+-independent-review\.md$"),
    re.compile(r"(^|/)QA-[^/]+/cycles/cycle-[0-9]+-verification\.md$"),
    re.compile(r"(^|/)QA-[^/]+/evidence/.*$"),
]

AUTHOR_WRITABLE_PATTERNS = [
    re.compile(r"(^|/)QA-[^/]+/cycles/cycle-[0-9]+-author-response\.md$"),
    re.compile(r"(^|/)QA-[^/]+/cycles/cycle-[0-9]+-submission\.json$"),
]


def is_path_allowed_for_write(rel_path: str, role: Literal["reviewer", "author"] = "reviewer") -> bool:
    """指定されたロールが指定されたパスへ書込み可能かを判定する。"""
    normalized = rel_path.replace("\\", "/").strip()
    if role == "reviewer":
        return any(pattern.search(normalized) is not None for pattern in REVIEWER_WRITABLE_PATTERNS)
    elif role == "author":
        return any(pattern.search(normalized) is not None for pattern in AUTHOR_WRITABLE_PATTERNS)
    return False


def check_write_permission(rel_path: str, role: Literal["reviewer", "author"] = "reviewer") -> None:
    """書込み許可を検証し、拒否された場合は PermissionError を送出する。"""
    if not is_path_allowed_for_write(rel_path, role):
        raise PermissionError(
            f"Write access denied for role '{role}' to path '{rel_path}'. "
            f"Path is not in the allowed write paths for {role}."
        )
