import pytest
from pathlib import Path
from spec_driven_qa_review.lifecycle import ReviewerLifecycle

def _touch(workspace, rel):
    p = Path(workspace) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("ok\n", encoding="utf-8")
    return rel

def test_cycle_limit_escalates_to_adjudication(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    lifecycle.init_case(case_id="QA-0501", target="src/app.py", purpose="docs/purpose.md", profile="standard")
    lifecycle.record_findings(case_id="QA-0501", findings=[
        {
            "id": "QA-0501-F01",
            "title": "Bug",
            "category": "logic-error",
            "severity": "high",
            "purpose_classification": "spec-required",
            "evidence": "src/app.py:L10",
        }
    ])
    lifecycle.render_handoff(case_id="QA-0501", cycle=1, case_revision="rev-001")
    _touch(tmp_path, "src/app.py")

    submission = {
        "finding_ids": ["QA-0501-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "All tests passed",
        "modified_files": ["src/app.py"],
    }
    res = lifecycle.verify_submission(case_id="QA-0501", submission=submission, cycle=3)
    assert res["status"] == "adjudication-required"

def test_close_case_success_with_verified_critical_and_open_low(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    lifecycle.init_case(case_id="QA-0502", target="src/app.py", purpose="docs/purpose.md")
    lifecycle.record_findings(case_id="QA-0502", findings=[
        {
            "id": "QA-0502-F01",
            "title": "Critical Data Bug",
            "category": "data-loss",
            "severity": "critical",
            "purpose_classification": "spec-required",
            "evidence": "src/app.py:L1",
        },
        {
            "id": "QA-0502-F02",
            "title": "Minor Typo",
            "category": "style",
            "severity": "low",
            "purpose_classification": "operational-hygiene",
            "evidence": "src/app.py:L99",
        }
    ])
    lifecycle.render_handoff(case_id="QA-0502", cycle=1, case_revision="rev-001")
    _touch(tmp_path, "src/app.py")

    submission = {
        "finding_ids": ["QA-0502-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "Verified with persistence test.",
        "modified_files": ["src/app.py"],
    }
    lifecycle.verify_submission(case_id="QA-0502", submission=submission, cycle=1)

    res = lifecycle.close_case(
        case_id="QA-0502",
        terminal_status="accepted-with-residual-risk",
        rationale="Critical bug fixed, minor typo accepted as residual risk.",
    )
    assert res["status"] == "success"
    assert res["terminal_status"] == "accepted-with-residual-risk"

def test_close_case_rejects_unresolved_markers_or_critical(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer")
    lifecycle.init_case(case_id="QA-0503", target="src/app.py", purpose="docs/purpose.md")

    case_dir = tmp_path / "QA-0503"
    with open(case_dir / "review.md", "a", encoding="utf-8") as f:
        f.write("\nREQUIRED:AUTHOR-RESPONSE:QA-0503-F01:CYCLE-1\n")

    with pytest.raises(ValueError, match="unresolved REQUIRED markers"):
        lifecycle.close_case(
            case_id="QA-0503",
            terminal_status="accepted",
        )

    review_clean = (case_dir / "review.md").read_text(encoding="utf-8").replace("REQUIRED:AUTHOR-RESPONSE:QA-0503-F01:CYCLE-1", "")
    (case_dir / "review.md").write_text(review_clean, encoding="utf-8")

    lifecycle.record_findings(case_id="QA-0503", findings=[
        {
            "id": "QA-0503-F01",
            "title": "Critical security bug",
            "category": "security-risk",
            "severity": "critical",
            "purpose_classification": "spec-required",
            "evidence": "src/app.py:L1",
        }
    ])

    with pytest.raises(ValueError, match="unresolved Critical findings"):
        lifecycle.close_case(
            case_id="QA-0503",
            terminal_status="accepted",
        )
