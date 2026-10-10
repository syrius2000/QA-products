"""loopを止めるべきかを、サイクルごとの未解決指摘から判定する。"""
from __future__ import annotations

from dataclasses import dataclass

MAX_CYCLES = 3


@dataclass(frozen=True)
class StopDecision:
    stop: bool
    reason: str


def decide_stop(unresolved_by_cycle: list[set[str]], cap: int = MAX_CYCLES, acknowledged: frozenset[str] = frozenset()) -> StopDecision:
    """acknowledged は、利用者が続行を承認した反復指摘のID。上限による停止は免除しない。"""
    if len(unresolved_by_cycle) >= 2 and (unresolved_by_cycle[-1] & unresolved_by_cycle[-2]) - acknowledged:
        return StopDecision(True, "同一指摘が連続2サイクル未解決")
    if len(unresolved_by_cycle) >= cap and unresolved_by_cycle[-1]:
        return StopDecision(True, "上限に到達し、未解決の指摘が残る")
    return StopDecision(False, "")
