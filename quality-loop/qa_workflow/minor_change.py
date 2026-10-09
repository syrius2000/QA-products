"""承認範囲内の軽微な変更を機械的に判定する。

AGENTS.md §3 に従い、対象パスの追加と行数では止めない。止めるのは完了条件・受入基準・確認方法の変更だけ。
対象パス外の変更はコミットに含めず、結果に一覧として残す。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ApprovedScope:
    paths: frozenset[str]
    contract_hash: str


@dataclass(frozen=True)
class ChangeSet:
    paths: frozenset[str]
    added_paths: frozenset[str]
    contract_hash: str


@dataclass(frozen=True)
class MinorDecision:
    minor: bool
    reasons: tuple[str, ...]
    outside_paths: tuple[str, ...] = ()


def judge_minor_change(approved: ApprovedScope, change: ChangeSet) -> MinorDecision:
    outside = tuple(sorted((change.paths | change.added_paths) - approved.paths))
    reasons = ()
    if change.contract_hash != approved.contract_hash:
        reasons = ("完了条件・受入基準・確認方法の変更",)
    return MinorDecision(minor=not reasons, reasons=reasons, outside_paths=outside)
