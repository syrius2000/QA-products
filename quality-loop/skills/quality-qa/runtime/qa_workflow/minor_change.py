"""承認範囲内の軽微な変更を機械的に判定する。"""
from __future__ import annotations

from dataclasses import dataclass

MINOR_LINE_LIMIT = 50


@dataclass(frozen=True)
class ApprovedScope:
    paths: frozenset[str]
    contract_hash: str


@dataclass(frozen=True)
class ChangeSet:
    paths: frozenset[str]
    added_paths: frozenset[str]
    contract_hash: str
    changed_lines: int


@dataclass(frozen=True)
class MinorDecision:
    minor: bool
    reasons: tuple[str, ...]


def judge_minor_change(approved: ApprovedScope, change: ChangeSet, line_limit: int) -> MinorDecision:
    reasons = []
    if not change.paths <= approved.paths:
        reasons.append("承認済み対象パス外の変更")
    if change.added_paths:
        reasons.append("新規パスの追加")
    if change.contract_hash != approved.contract_hash:
        reasons.append("完了条件・受入基準・確認方法の変更")
    if change.changed_lines > line_limit:
        reasons.append("変更行数が上限を超える")
    return MinorDecision(minor=not reasons, reasons=tuple(reasons))
