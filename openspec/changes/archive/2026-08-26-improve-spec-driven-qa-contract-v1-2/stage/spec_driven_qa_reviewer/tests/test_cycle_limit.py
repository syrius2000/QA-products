import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

import pytest

from spec_driven_qa_reviewer.scripts.cycle_limit import cycle_limit, evaluate_cycle


@pytest.mark.parametrize("profile,limit", [("lite", 1), ("standard", 2), ("strict", 3)])
def test_cycle_limits(profile, limit):
    assert cycle_limit(profile) == limit
    result = evaluate_cycle(profile, limit)
    assert result["status"] == "escalate"
    assert result["next_action"] == "owner-decision"
    assert result["auto_close"] is False


def test_cycle_below_limit_continues():
    result = evaluate_cycle("standard", 1)
    assert result["status"] == "continue"
    assert result["auto_close"] is False


def test_unknown_profile_is_rejected():
    with pytest.raises(ValueError):
        cycle_limit("unbounded")
