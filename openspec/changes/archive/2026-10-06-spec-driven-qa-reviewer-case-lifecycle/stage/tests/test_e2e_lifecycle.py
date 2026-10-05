import json
from pathlib import Path
from spec_driven_qa_review.lifecycle import ReviewerLifecycle

def test_full_lifecycle_e2e(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    case_id = "QA-0901-e2e-feature"

    res_init = lifecycle.init_case(
        case_id=case_id,
        target="src/sensor_collector.py",
        purpose="docs/specs/iot-collector.md",
        profile="proportional-home",
        title="IoT Sensor Collector Review",
    )
    assert res_init["status"] == "success"

    findings = [
        {
            "id": "QA-0901-F01",
            "title": "Unbounded memory queue lost on device restart",
            "category": "data-loss",
            "severity": "critical",
            "purpose_classification": "purpose-critical",
            "evidence": "src/sensor_collector.py:L34-40",
        },
        {
            "id": "QA-0901-F02",
            "title": "Missing mTLS in home LAN environment",
            "category": "security-risk",
            "severity": "low",
            "purpose_classification": "operational-hygiene",
            "evidence": "src/sensor_collector.py:L70",
        }
    ]
    res_review = lifecycle.record_findings(case_id=case_id, findings=findings, cycle=1)
    assert res_review["status"] == "success"

    res_handoff = lifecycle.render_handoff(case_id=case_id, cycle=1, case_revision="rev-001")
    assert res_handoff["status"] == "success"
    assert "QA-0901-F01" in res_handoff["open_findings"]

    fix = tmp_path / "src" / "sensor_collector.py"
    fix.parent.mkdir(parents=True, exist_ok=True)
    fix.write_text("# fixed\n", encoding="utf-8")

    submission = {
        "finding_ids": ["QA-0901-F01", "QA-0901-F02"],
        "base_revision": "rev-001",
        "result_revision": "rev-002",
        "status": "fix-submitted",
        "test_evidence": "Added sqlite disk spool test and verified persistence.",
        "modified_files": ["src/sensor_collector.py"],
    }
    res_verify = lifecycle.verify_submission(case_id=case_id, submission=submission, cycle=1)
    assert res_verify["status"] == "success"

    res_close = lifecycle.close_case(
        case_id=case_id,
        terminal_status="accepted",
        rationale="Critical data loss queue issue verified fixed on disk spool.",
    )
    assert res_close["status"] == "success"
    assert res_close["terminal_status"] == "accepted"

    case_dir = tmp_path / case_id
    assert (case_dir / "review.md").exists()
    assert (case_dir / "findings.yaml").exists()
    assert (case_dir / "traceability.yaml").exists()
    assert (case_dir / "handoff.md").exists()
    assert (case_dir / "cycles" / "cycle-01-independent-review.md").exists()
    assert (case_dir / "cycles" / "cycle-01-verification.md").exists()

    events = [json.loads(line) for line in (case_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]
    assert len(events) == 5
    assert [e["action"] for e in events] == ["init", "review", "handoff", "verify", "close"]
