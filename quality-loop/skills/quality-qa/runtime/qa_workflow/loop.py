"""承認済み修正をcommit・提出・公開・再QA依頼まで進める。判定は行わない。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .loop_guard import decide_stop
from .loop_stages import run_stages
from .minor_change import MinorDecision
from .repair_commit import COMMIT_PHRASE
from .store import QAError

CLOUD_PHRASE = "クラウドQAに出して"


@dataclass(frozen=True)
class LoopResult:
    status: str
    reason: str
    done: dict


def run_loop(
    phase: str,
    approval_text: str,
    done: dict,
    actions: dict[str, Callable[[], dict]],
    save: Callable[..., None],
    unresolved_history: list[set[str]],
    minor: MinorDecision | None = None,
    cloud_authorized: bool | None = None,
) -> LoopResult:
    if phase != "approved":
        return LoopResult("waiting_approval", "承認前のため修正を行いません。計画を確認して承認してください", done)
    stop = decide_stop(unresolved_history)
    if stop.stop:
        return LoopResult("stopped", stop.reason, done)
    if minor is not None and not minor.minor:
        return LoopResult("stopped", "承認範囲外の変更: " + "、".join(minor.reasons), done)
    if COMMIT_PHRASE not in approval_text:
        return LoopResult("stopped", f"承認文に「{COMMIT_PHRASE}」が必要です", done)
    cloud = CLOUD_PHRASE in approval_text if cloud_authorized is None else cloud_authorized
    stop_before = None if cloud else "push"
    latest = {"done": dict(done)}

    def track(progress: dict, failed: dict | None = None) -> None:
        latest["done"] = dict(progress)
        save(progress, failed=failed)

    try:
        progress = run_stages(done, actions, track, stop_before=stop_before)
    except QAError as error:
        return LoopResult("failed", f"{error}。{error.action}", latest["done"])
    if stop_before and stop_before not in progress:
        return LoopResult("stopped", f"公開と再QA依頼の前で停止しました。「{CLOUD_PHRASE}」を含む承認が必要です", progress)
    return LoopResult("completed", "再QA依頼まで完了しました", progress)
