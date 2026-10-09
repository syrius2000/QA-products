"""loopの段階を順に実行し、完了した段階だけを記録して途中から再開する。"""
from __future__ import annotations

from typing import Callable

from .store import QAError

STAGES = ("commit", "submit", "push", "ancestry", "requa-request", "finalize", "publish")


def run_stages(done: dict, actions: dict[str, Callable[[], dict]], save: Callable[..., None], stop_before: str | None = None) -> dict:
    progress = dict(done)
    for name in STAGES:
        if name == stop_before:
            break
        if name in progress:
            continue
        try:
            progress[name] = actions[name]()
        except QAError as error:
            save(progress, failed={"stage": name, "reason": str(error), "action": error.action})
            raise
        save(progress, failed=None)
    return progress


def stage_status(done: dict, failed: dict | None) -> dict:
    completed = [name for name in STAGES if name in done]
    pending = [name for name in STAGES if name not in done]
    return {
        "completed": completed,
        "failed": failed,
        "next": pending[0] if pending else None,
    }
