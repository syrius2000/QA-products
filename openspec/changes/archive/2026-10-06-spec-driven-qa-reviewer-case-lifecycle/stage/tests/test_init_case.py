import json
import pytest
from spec_driven_qa_review.lifecycle import ReviewerLifecycle

def test_init_case_success(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer")
    res = lifecycle.init_case(
        case_id="QA-0101-test-feature",
        target="src/feature.py",
        purpose="docs/specs/feature-spec.md",
        profile="standard",
        title="Test Feature QA",
    )
    assert res["status"] == "success"
    case_dir = tmp_path / "QA-0101-test-feature"
    assert (case_dir / "review.md").exists()
    assert (case_dir / "findings.yaml").exists()
    assert (case_dir / "traceability.yaml").exists()
    assert (case_dir / "events.jsonl").exists()

    events = [json.loads(line) for line in (case_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]
    assert len(events) == 1
    assert events[0]["action"] == "init"
    assert events[0]["role"] == "reviewer"

def test_init_case_missing_target_or_purpose(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer")
    with pytest.raises(ValueError, match="Target file"):
        lifecycle.init_case(case_id="QA-0102", target="", purpose="docs/purpose.md")
    
    with pytest.raises(ValueError, match="Purpose"):
        lifecycle.init_case(case_id="QA-0102", target="src/main.py", purpose="")

    assert not (tmp_path / "QA-0102").exists()

def test_init_case_invalid_profile(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer")
    with pytest.raises(ValueError, match="Invalid profile"):
        lifecycle.init_case(case_id="QA-0103", target="src/main.py", purpose="docs/purpose.md", profile="invalid-prof")
