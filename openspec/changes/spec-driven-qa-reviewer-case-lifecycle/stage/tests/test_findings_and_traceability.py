import json
import pytest
from spec_driven_qa_review.lifecycle import ReviewerLifecycle

def test_record_findings_success(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer")
    lifecycle.init_case(case_id="QA-0201", target="src/app.py", purpose="docs/purpose.md")
    
    findings = [
        {
            "id": "QA-0201-F01",
            "title": "Unbounded queue loss on restart",
            "category": "data-loss",
            "severity": "critical",
            "purpose_classification": "purpose-critical",
            "evidence": "src/app.py:L45-50",
        },
        {
            "id": "QA-0201-F02",
            "title": "Missing non-essential auth header in home profile",
            "category": "security-risk",
            "severity": "low",
            "purpose_classification": "operational-hygiene",
            "evidence": "src/app.py:L80",
        }
    ]
    res = lifecycle.record_findings(case_id="QA-0201", findings=findings, cycle=1)
    assert res["status"] == "success"
    assert res["findings_count"] == 2

    case_dir = tmp_path / "QA-0201"
    assert (case_dir / "cycles" / "cycle-01-independent-review.md").exists()
    
    events = [json.loads(line) for line in (case_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]
    assert len(events) == 2
    assert events[1]["action"] == "review"
    assert events[1]["findings_count"] == 2

def test_record_findings_missing_evidence_or_classification_rejected(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer")
    lifecycle.init_case(case_id="QA-0202", target="src/app.py", purpose="docs/purpose.md")
    
    case_dir = tmp_path / "QA-0202"
    orig_findings = (case_dir / "findings.yaml").read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="evidence references"):
        lifecycle.record_findings(case_id="QA-0202", findings=[{
            "id": "QA-0202-F01",
            "category": "spec-drift",
            "severity": "high",
            "purpose_classification": "spec-required",
            "evidence": "",
        }])
    
    with pytest.raises(ValueError, match="purpose_classification"):
        lifecycle.record_findings(case_id="QA-0202", findings=[{
            "id": "QA-0202-F02",
            "category": "spec-drift",
            "severity": "high",
            "purpose_classification": "invalid-class",
            "evidence": "src/app.py:L10",
        }])

    assert (case_dir / "findings.yaml").read_text(encoding="utf-8") == orig_findings
