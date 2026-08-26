import json
import pytest
from spec_driven_qa_review.lifecycle import ReviewerLifecycle

def test_render_handoff(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer")
    lifecycle.init_case(case_id="QA-0301", target="src/module.py", purpose="docs/purpose.md")
    lifecycle.record_findings(case_id="QA-0301", findings=[
        {
            "id": "QA-0301-F01",
            "title": "Invalid timestamp format",
            "category": "data-quality",
            "severity": "high",
            "purpose_classification": "spec-required",
            "evidence": "src/module.py:L20",
        }
    ])

    res = lifecycle.render_handoff(case_id="QA-0301", cycle=1, case_revision="rev-001")
    assert res["status"] == "success"
    assert res["open_findings"] == ["QA-0301-F01"]

    case_dir = tmp_path / "QA-0301"
    handoff_text = (case_dir / "handoff.md").read_text(encoding="utf-8")
    assert 'schema_version: "1.2"' in handoff_text
    assert "case_id: QA-0301" in handoff_text
    assert "origin_role: reviewer" in handoff_text
    assert "implementation_permission: scoped" in handoff_text
    assert "QA-0301-F01" in handoff_text
