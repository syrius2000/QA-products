import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.digest import canonical_json, semantic_digest


def base_case():
    return {
        "contract_version": "1.2",
        "schema_version": "qa-case-v1.2",
        "case_id": "QA-0001",
        "case_status": "verification-in-progress",
        "next_action": "reviewer-verification",
        "case_revision": 2,
        "quality_intent": {"criticality": "home-monitoring"},
        "target_scope": ["src/app.py"],
        "terminal_result": None,
        "generated_at": "2026-08-25T21:00:00+09:00",
        "events": [{"action": "created"}],
        "findings": [
            {
                "id": "QA-0001-F02",
                "severity": "low",
                "finding_status": "open",
                "technical_status": "unverified",
                "required_evidence": ["test"],
                "implementation_permission": "none",
                "base_revision": "abc",
                "description": "表示用説明",
            },
            {
                "id": "QA-0001-F01",
                "severity": "medium",
                "finding_status": "awaiting-author",
                "technical_status": "partially-fixed",
                "required_evidence": ["runtime"],
                "implementation_permission": "scoped",
                "base_revision": "abc",
            },
        ],
    }


def test_semantic_digest_ignores_mapping_and_finding_order():
    first = base_case()
    second = base_case()
    second["findings"] = list(reversed(second["findings"]))
    second["quality_intent"] = {"criticality": "home-monitoring"}
    assert semantic_digest(first) == semantic_digest(second)


def test_semantic_digest_ignores_display_and_event_changes():
    first = base_case()
    second = base_case()
    second["generated_at"] = "2026-08-25T22:00:00+09:00"
    second["events"] = [{"action": "verified"}]
    second["findings"][0]["description"] = "説明本文だけを変更"
    assert semantic_digest(first) == semantic_digest(second)


def test_semantic_digest_changes_when_severity_changes():
    first = base_case()
    second = base_case()
    second["findings"][0]["severity"] = "high"
    assert semantic_digest(first) != semantic_digest(second)


def test_canonical_json_is_compact_and_key_sorted():
    canonical = canonical_json(base_case())
    assert canonical.index('"case_id"') < canonical.index('"findings"')
    assert "generated_at" not in canonical
    assert " " not in canonical
