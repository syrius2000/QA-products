"""Contract v1.2の二重digestと楽観的比較更新を検証する。"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from .digest import semantic_digest


def content_digest(contents: Mapping[str, str]) -> str:
    """ファイル名順に内容を連結し、改行だけ正規化したdigestを返す。"""
    digest = hashlib.sha256()
    for name in sorted(contents):
        normalized = contents[name].replace("\r\n", "\n").replace("\r", "\n")
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(normalized.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def classify_handoff_freshness(
    *,
    expected_semantic: str,
    actual_semantic: str,
    expected_content: str,
    actual_content: str,
) -> dict[str, Any]:
    if expected_semantic != actual_semantic:
        return {
            "status": "blocked",
            "code": "inconsistent-qa-state",
            "next_action": "regenerate-handoff",
        }
    if expected_content != actual_content:
        return {
            "status": "warning",
            "code": "content-changed",
            "next_action": "regenerate-and-human-confirm",
        }
    return {"status": "accepted", "code": None, "next_action": "continue"}


def validate_optimistic_update(
    current: dict[str, Any],
    proposed: dict[str, Any],
    *,
    expected_semantic_digest: str,
    expected_case_revision: int,
) -> list[str]:
    """古い正本からの提出やrevision飛び越しを拒否する。"""
    errors: list[str] = []
    actual_digest = semantic_digest(current)
    if actual_digest != expected_semantic_digest:
        errors.append("blocked: inconsistent-qa-state")
    current_revision = current.get("case_revision")
    if current_revision != expected_case_revision:
        errors.append("blocked: stale-case-revision")
    proposed_revision = proposed.get("case_revision")
    if proposed_revision != expected_case_revision + 1:
        errors.append("proposed case_revision must increment by one")
    return errors
