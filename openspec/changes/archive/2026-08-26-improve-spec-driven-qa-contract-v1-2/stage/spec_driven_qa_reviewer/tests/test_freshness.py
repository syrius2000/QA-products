import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.digest import semantic_digest
from spec_driven_qa_reviewer.scripts.freshness import (
    classify_handoff_freshness,
    content_digest,
    validate_optimistic_update,
)


def case():
    return {
        "contract_version": "1.2",
        "case_id": "QA-0001",
        "case_status": "author-action-required",
        "next_action": "author-response",
        "case_revision": 4,
        "findings": [],
        "terminal_result": None,
    }


def test_content_digest_normalizes_only_line_endings():
    first = {"review.md": "status: open\n  body: x\n"}
    second = {"review.md": "status: open\r\n  body: x\r\n"}
    assert content_digest(first) == content_digest(second)
    assert content_digest(first) != content_digest({"review.md": "status: open\n body: x\n"})


def test_semantic_mismatch_blocks_handoff():
    result = classify_handoff_freshness(
        expected_semantic="old",
        actual_semantic="new",
        expected_content="same",
        actual_content="same",
    )
    assert result == {
        "status": "blocked",
        "code": "inconsistent-qa-state",
        "next_action": "regenerate-handoff",
    }


def test_content_only_mismatch_requires_confirmation():
    result = classify_handoff_freshness(
        expected_semantic="same",
        actual_semantic="same",
        expected_content="old-content",
        actual_content="new-content",
    )
    assert result["status"] == "warning"
    assert result["next_action"] == "regenerate-and-human-confirm"


def test_optimistic_update_accepts_current_revision():
    current = case()
    proposed = {**current, "case_revision": 5}
    assert validate_optimistic_update(
        current,
        proposed,
        expected_semantic_digest=semantic_digest(current),
        expected_case_revision=4,
    ) == []


def test_optimistic_update_rejects_stale_and_skipped_revision():
    current = case()
    proposed = {**current, "case_revision": 7}
    errors = validate_optimistic_update(
        current,
        proposed,
        expected_semantic_digest="stale",
        expected_case_revision=3,
    )
    assert "blocked: inconsistent-qa-state" in errors
    assert "blocked: stale-case-revision" in errors
    assert "proposed case_revision must increment by one" in errors
