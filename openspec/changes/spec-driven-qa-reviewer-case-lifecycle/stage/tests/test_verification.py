import pytest
from pathlib import Path
from spec_driven_qa_review.lifecycle import ReviewerLifecycle

def _touch(workspace, rel):
    p = Path(workspace) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("ok\n", encoding="utf-8")
    return rel

def test_verify_submission_success(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    lifecycle.init_case(case_id="QA-0401", target="src/main.py", purpose="docs/purpose.md")
    lifecycle.record_findings(case_id="QA-0401", findings=[
        {
            "id": "QA-0401-F01",
            "title": "Unchecked return",
            "category": "logic-error",
            "severity": "medium",
            "purpose_classification": "spec-required",
            "evidence": "src/main.py:L12",
        }
    ])
    lifecycle.render_handoff(case_id="QA-0401", cycle=1, case_revision="rev-001")
    _touch(tmp_path, "src/main.py")

    submission = {
        "finding_ids": ["QA-0401-F01"],
        "base_revision": "rev-001",
        "result_revision": "rev-002",
        "status": "fix-submitted",
        "test_evidence": "Added test_main_return check and passed.",
        "modified_files": ["src/main.py"],
    }
    res = lifecycle.verify_submission(case_id="QA-0401", submission=submission, cycle=1)
    assert res["status"] == "success"
    assert res["outcome"] == "verified"
    assert (tmp_path / "QA-0401" / "cycles" / "cycle-01-verification.md").exists()

def test_verify_submission_rejects_missing_handoff_or_base_revision(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    lifecycle.init_case(case_id="QA-0402", target="src/main.py", purpose="docs/purpose.md")
    lifecycle.record_findings(case_id="QA-0402", findings=[
        {
            "id": "QA-0402-F01",
            "title": "Bug",
            "category": "logic-error",
            "severity": "high",
            "purpose_classification": "spec-required",
            "evidence": "src/main.py:L10",
        }
    ])
    _touch(tmp_path, "src/main.py")

    submission = {
        "finding_ids": ["QA-0402-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "pytest passed",
        "modified_files": ["src/main.py"],
    }
    with pytest.raises(ValueError, match="handoff.md is required"):
        lifecycle.verify_submission(case_id="QA-0402", submission=submission, cycle=1)

    lifecycle.render_handoff(case_id="QA-0402", cycle=1, case_revision="rev-001")
    submission_no_base = {
        "finding_ids": ["QA-0402-F01"],
        "status": "fix-submitted",
        "test_evidence": "pytest passed",
        "modified_files": ["src/main.py"],
    }
    with pytest.raises(ValueError, match="lacks required base_revision"):
        lifecycle.verify_submission(case_id="QA-0402", submission=submission_no_base, cycle=1)

def test_verify_submission_rejects_self_close(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    lifecycle.init_case(case_id="QA-0403", target="src/main.py", purpose="docs/purpose.md")
    lifecycle.record_findings(case_id="QA-0403", findings=[
        {
            "id": "QA-0403-F01",
            "title": "Bug",
            "category": "logic-error",
            "severity": "high",
            "purpose_classification": "spec-required",
            "evidence": "src/main.py:L10",
        }
    ])
    lifecycle.render_handoff(case_id="QA-0403", cycle=1, case_revision="rev-001")
    _touch(tmp_path, "src/main.py")

    submission = {
        "finding_ids": ["QA-0403-F01"],
        "base_revision": "rev-001",
        "status": "fixed-and-verified",
        "test_evidence": "I verified it myself",
        "modified_files": ["src/main.py"],
    }
    with pytest.raises(ValueError, match="Author cannot self-close or self-verify"):
        lifecycle.verify_submission(case_id="QA-0403", submission=submission, cycle=1)
