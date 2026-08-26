import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.validate_contract_v1_2 import validate_document


def valid_case():
    return {
        "contract_version": "1.2",
        "case_id": "QA-0001",
        "case_status": "verification-in-progress",
        "next_action": "reviewer-verification",
        "case_revision": 2,
        "findings": [{
            "id": "QA-0001-F01",
            "severity": "medium",
            "finding_status": "verification-required",
            "technical_status": "partially-fixed",
            "author_disposition": "fix-submitted",
            "owner_disposition": None,
        }],
        "terminal_result": None,
    }


def test_valid_contract_is_accepted():
    assert validate_document(valid_case()) == []


def test_closed_case_requires_terminal_result():
    document = valid_case()
    document["case_status"] = "closed"
    assert "closed case requires terminal_result" in validate_document(document)


def test_unknown_case_state_is_rejected():
    document = valid_case()
    document["case_status"] = "self-closed"
    assert any("invalid case_status" in error for error in validate_document(document))


def test_unknown_top_level_state_is_rejected():
    document = valid_case()
    document["workflow_phase"] = "verification"
    assert any("unknown top-level field" in error for error in validate_document(document))
