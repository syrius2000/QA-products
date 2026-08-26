"""Reviewer lifecycleの共有コアを明示的な相対位置から読むAdapter。"""

from __future__ import annotations

import sys
from pathlib import Path


def _shared_stage() -> Path:
    # .../openspec/changes/<this-change>/stage/<package>/file.py
    return Path(__file__).resolve().parents[3] / "spec-driven-qa-reviewer-case-lifecycle" / "stage"


def load_shared_core():
    stage = _shared_stage()
    if not stage.is_dir():
        raise RuntimeError(f"shared core is unavailable: {stage}")
    stage_text = str(stage)
    if stage_text not in sys.path:
        sys.path.insert(0, stage_text)
    from shared_core.digest import content_digest
    from shared_core.authorization import allowed

    return content_digest, allowed


def load_handoff_digests():
    stage = _shared_stage()
    if not stage.is_dir():
        raise RuntimeError(f"shared core is unavailable: {stage}")
    stage_text = str(stage)
    if stage_text not in sys.path:
        sys.path.insert(0, stage_text)
    from shared_core.digest import handoff_digests

    return handoff_digests


def load_handoff_content_digest():
    stage = _shared_stage()
    if not stage.is_dir():
        raise RuntimeError(f"shared core is unavailable: {stage}")
    stage_text = str(stage)
    if stage_text not in sys.path:
        sys.path.insert(0, stage_text)
    from shared_core.digest import handoff_content_digest

    return handoff_content_digest


def load_digest_version_validator():
    stage = _shared_stage()
    if not stage.is_dir():
        raise RuntimeError(f"shared core is unavailable: {stage}")
    stage_text = str(stage)
    if stage_text not in sys.path:
        sys.path.insert(0, stage_text)
    from shared_core.digest import validate_digest_version

    return validate_digest_version
