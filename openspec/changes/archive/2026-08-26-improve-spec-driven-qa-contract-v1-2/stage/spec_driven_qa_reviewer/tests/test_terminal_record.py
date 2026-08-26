import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.terminal_record import (
    is_technical_completion,
    validate_terminal_record,
)


def record():
    return {
        "owner": "owner-1",
        "rationale": "実行環境を準備できない",
        "scope_or_assumptions": "stage環境のみ",
        "compensating_controls": ["再レビューを要求する"],
        "expiry_or_review_trigger": "実機接続時",
    }


def test_non_technical_result_requires_owner_record():
    assert validate_terminal_record("evidence-gap", record()) == []
    assert is_technical_completion("evidence-gap") is False


def test_missing_re_review_condition_is_rejected():
    document = record()
    document["expiry_or_review_trigger"] = ""
    assert any("expiry_or_review_trigger" in error for error in validate_terminal_record("deferred", document))


def test_empty_compensating_controls_are_rejected():
    document = record()
    document["compensating_controls"] = []
    assert any("compensating_controls" in error for error in validate_terminal_record("risk-accepted", document))


def test_fixed_and_verified_is_technical_completion():
    assert validate_terminal_record("fixed-and-verified", {}) == []
    assert is_technical_completion("fixed-and-verified") is True
