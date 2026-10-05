import pytest
from spec_driven_qa_review.allowlist import is_path_allowed_for_write, check_write_permission
from shared_core.authorization import REVIEWER_OPERATIONS, AUTHOR_OPERATIONS, allowed

def test_reviewer_writable_paths():
    valid_paths = [
        "docs/ADR/QA/QA-0001/review.md",
        "docs/ADR/QA/QA-0001/findings.yaml",
        "docs/ADR/QA/QA-0001/traceability.yaml",
        "docs/ADR/QA/QA-0001/events.jsonl",
        "docs/ADR/QA/QA-0001/handoff.md",
        "docs/ADR/QA/QA-0001/cycles/cycle-01-independent-review.md",
        "docs/ADR/QA/QA-0001/cycles/cycle-01-verification.md",
        "docs/ADR/QA/QA-0001/evidence/test-run.log",
    ]
    for p in valid_paths:
        assert is_path_allowed_for_write(p, "reviewer") is True
        check_write_permission(p, "reviewer")

def test_reviewer_rejects_unallowed_paths():
    invalid_paths = [
        "src/main.py",
        "docs/ADR/QA/QA-0001/cycles/cycle-01-author-response.md",
        "docs/ADR/QA/QA-0001/cycles/cycle-01-submission.json",
        "README.md",
        "openspec/specs/auth/spec.md",
    ]
    for p in invalid_paths:
        assert is_path_allowed_for_write(p, "reviewer") is False
        with pytest.raises(PermissionError):
            check_write_permission(p, "reviewer")

def test_author_cannot_write_reviewer_canonical_files():
    forbidden_for_author = [
        "docs/ADR/QA/QA-0001/review.md",
        "docs/ADR/QA/QA-0001/findings.yaml",
        "docs/ADR/QA/QA-0001/traceability.yaml",
        "docs/ADR/QA/QA-0001/events.jsonl",
        "docs/ADR/QA/QA-0001/handoff.md",
        "docs/ADR/QA/QA-0001/cycles/cycle-01-independent-review.md",
        "docs/ADR/QA/QA-0001/cycles/cycle-01-verification.md",
    ]
    for p in forbidden_for_author:
        assert is_path_allowed_for_write(p, "author") is False
        with pytest.raises(PermissionError):
            check_write_permission(p, "author")

def test_operations_mapping():
    assert REVIEWER_OPERATIONS == frozenset({"review", "handoff", "verify", "close"})
    assert AUTHOR_OPERATIONS == frozenset({"respond", "submit"})
    assert allowed("reviewer", "review") is True
    assert allowed("reviewer", "handoff") is True
    assert allowed("reviewer", "verify") is True
    assert allowed("reviewer", "close") is True
    assert allowed("author", "review") is False
