import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.state_machine import (
    derive_terminal_result,
    derive_workflow_phase,
    validate_state,
)


def state(status="author-action-required", action="author-response", terminal=None):
    return {
        "case_status": status,
        "next_action": action,
        "case_revision": 1,
        "terminal_result": terminal,
    }


def test_author_phase_is_derived():
    document = state()
    assert validate_state(document) == []
    assert derive_workflow_phase(document) == "author-response"
    assert derive_terminal_result(document) is None


def test_closed_terminal_state_is_derived():
    document = state("closed", "none", "evidence-gap")
    assert validate_state(document) == []
    assert derive_workflow_phase(document) == "terminal"
    assert derive_terminal_result(document) == "evidence-gap"


def test_invalid_status_action_combination_is_rejected():
    errors = validate_state(state("verification-in-progress", "author-response"))
    assert any("invalid for case_status" in error for error in errors)


def test_persisted_workflow_phase_is_rejected():
    document = state()
    document["workflow_phase"] = "author-response"
    assert any("must be derived" in error for error in validate_state(document))


def test_non_terminal_result_cannot_be_persisted_before_close():
    errors = validate_state(state("verification-in-progress", "reviewer-verification", "deferred"))
    assert any("only valid for closed" in error for error in errors)
