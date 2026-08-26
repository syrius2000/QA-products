import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.digest import semantic_digest
from spec_driven_qa_reviewer.scripts.evidence import validate_evidence_bundle
from spec_driven_qa_reviewer.scripts.submission_validator import (
    accept_author_submission,
    submission_hash,
)


def case():
    return {
        "contract_version": "1.2",
        "case_id": "QA-0001",
        "case_status": "author-action-required",
        "next_action": "author-response",
        "case_revision": 2,
        "findings": [{"id": "QA-0001-F01", "severity": "medium", "finding_status": "awaiting-author"}],
        "terminal_result": None,
    }


def evidence():
    return {
        "required_evidence": [{"id": "test", "description": "テスト結果"}],
        "evidence": [{
            "id": "EV-01", "reference": "tests/test_contract.py", "reference_type": "repository-relative",
            "verifier": "author", "acquired_at": "2026-08-25T21:00:00+09:00",
            "result": "verified", "secret_status": "none",
        }],
    }


def submission():
    result = {
        "submission_id": "submission-001",
        "base_revision": 2,
        "expected_semantic_digest": semantic_digest(case()),
        "target_findings": ["QA-0001-F01"],
        "author_response": "修正を提出しました",
        "evidence": evidence(),
    }
    result["submission_hash"] = submission_hash(result)
    return result


def test_valid_submission_produces_candidate_only():
    result = accept_author_submission(case(), submission())
    assert result["accepted"] is True
    assert result["candidate"]["submission_id"] == "submission-001"


def test_stale_revision_is_rejected():
    document = submission()
    document["base_revision"] = 1
    document["submission_hash"] = submission_hash(document)
    result = accept_author_submission(case(), document)
    assert result["accepted"] is False
    assert "base revision is stale" in result["errors"]


def test_unknown_finding_is_rejected():
    document = submission()
    document["target_findings"] = ["QA-0001-F99"]
    document["submission_hash"] = submission_hash(document)
    result = accept_author_submission(case(), document)
    assert result["accepted"] is False
    assert "submission targets an unknown Finding" in result["errors"]


def test_duplicate_submission_id_is_rejected():
    result = accept_author_submission(case(), submission(), accepted_submission_ids={"submission-001"})
    assert result["accepted"] is False
    assert "submission_id has already been accepted" in result["errors"]
