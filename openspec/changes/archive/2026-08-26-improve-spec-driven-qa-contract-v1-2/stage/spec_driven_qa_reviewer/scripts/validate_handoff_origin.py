"""handoffがReviewer正本から生成された内容かを検証する。"""

from __future__ import annotations

from pathlib import Path

from spec_driven_qa_reviewer.scripts.render_handoff import comparable, render


def validate_handoff_origin(case: Path, handoff: Path | None = None) -> list[str]:
    handoff_path = handoff or (case / "handoff.md")
    if not handoff_path.exists():
        return [f"handoff is missing: {handoff_path}"]
    expected = comparable(render(case))
    actual = comparable(handoff_path.read_text(encoding="utf-8"))
    if actual != expected:
        return ["handoff must be generated from the Reviewer canonical case"]
    return []
