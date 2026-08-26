import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_author_response.scripts.validate_author_response import validate_handoff_submission


HANDOFF = '''---
contract_version: "1.2"
case_id: QA-0001
case_revision: 2
semantic_digest: "abc"
implementation_permission: "scoped"
---

| QA-0001-F01 | medium | open | 対応 | - |
'''


def valid_submission():
    return {
        "base_revision": 2,
        "expected_semantic_digest": "abc",
        "target_findings": ["QA-0001-F01"],
        "responses": {"QA-0001-F01": {"disposition": "fix-submitted"}},
        "implementation": {"files": ["src/app.py"]},
    }


def test_valid_handoff_submission_is_accepted():
    assert validate_handoff_submission(HANDOFF, valid_submission()) == []


def test_unknown_finding_is_rejected():
    submission = valid_submission()
    submission["target_findings"] = ["QA-0001-F99"]
    assert any("unknown Finding" in error for error in validate_handoff_submission(HANDOFF, submission))


def test_unanswered_finding_is_rejected():
    submission = valid_submission()
    submission["responses"] = {}
    assert any("unanswered Finding" in error for error in validate_handoff_submission(HANDOFF, submission))


def test_missing_revision_and_digest_are_rejected():
    submission = valid_submission()
    del submission["base_revision"]
    del submission["expected_semantic_digest"]
    errors = validate_handoff_submission(HANDOFF, submission)
    assert "base_revision is required" in errors
    assert "expected_semantic_digest is required" in errors


def test_implementation_without_permission_is_rejected():
    handoff = HANDOFF.replace('implementation_permission: "scoped"', 'implementation_permission: "none"')
    assert any("not permitted" in error for error in validate_handoff_submission(handoff, valid_submission()))
