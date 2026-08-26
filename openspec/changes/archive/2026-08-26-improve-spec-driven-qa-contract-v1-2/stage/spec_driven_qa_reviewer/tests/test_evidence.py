import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.evidence import is_success, validate_evidence_bundle


def record(result="verified"):
    return {
        "id": "EV-001",
        "reference": "tests/test_contract.py:10",
        "reference_type": "repository-relative",
        "verifier": "reviewer",
        "acquired_at": "2026-08-25T21:00:00+09:00",
        "result": result,
        "secret_status": "none",
        "summary": "fixture test passed",
    }


def bundle(result="verified"):
    return {
        "required_evidence": [{"id": "runtime", "description": "実行結果"}],
        "evidence": [record(result)],
    }


def test_verified_evidence_is_success():
    assert validate_evidence_bundle(bundle()) == []
    assert is_success(record()) is True


def test_unverified_and_evidence_gap_are_not_success():
    for result in ("unverified", "evidence-gap"):
        assert validate_evidence_bundle(bundle(result)) == []
        assert is_success(record(result)) is False


def test_missing_verifier_is_rejected():
    document = bundle()
    del document["evidence"][0]["verifier"]
    assert any("verifier" in error for error in validate_evidence_bundle(document))


def test_unmasked_secret_is_rejected():
    document = bundle()
    document["evidence"][0]["summary"] = "token=super-secret-value"
    assert any("unmasked secret" in error for error in validate_evidence_bundle(document))


def test_rejected_secret_status_is_not_accepted():
    document = bundle()
    document["evidence"][0]["secret_status"] = "rejected"
    assert any("must not be submitted" in error for error in validate_evidence_bundle(document))
