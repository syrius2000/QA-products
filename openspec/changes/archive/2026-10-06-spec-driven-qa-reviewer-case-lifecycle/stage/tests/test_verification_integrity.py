import re
import pytest
from pathlib import Path
from spec_driven_qa_review.lifecycle import (
    ReviewerLifecycle,
    compute_handoff_digests,
    classify_evidence_ref,
)


def _seed_case(lifecycle, case_id, finding_id="F01"):
    lifecycle.init_case(case_id=case_id, target="src/main.py", purpose="docs/purpose.md")
    lifecycle.record_findings(
        case_id=case_id,
        findings=[
            {
                "id": f"{case_id}-{finding_id}",
                "title": "Bug",
                "category": "logic-error",
                "severity": "medium",
                "purpose_classification": "spec-required",
                "evidence": "src/main.py:L12",
            }
        ],
    )
    return lifecycle.render_handoff(case_id=case_id, cycle=1, case_revision="rev-001")


def _touch(workspace: Path, rel: str) -> str:
    p = workspace / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("ok\n", encoding="utf-8")
    return rel


def test_compute_handoff_digests_stable():
    a = compute_handoff_digests("QA-0001", ["QA-0001-F01"], 1)
    b = compute_handoff_digests("QA-0001", ["QA-0001-F01"], 1)
    assert a == b
    assert a["content_digest"] != a["semantic_digest"]
    assert a["content_digest"]


def test_semantic_change_is_distinguished():
    a = compute_handoff_digests("QA-0001", ["QA-0001-F01"], 1, "rev-001")
    b = compute_handoff_digests("QA-0001", ["QA-0001-F01"], 1, "rev-002")
    assert a["semantic_digest"] != b["semantic_digest"]
    assert a["content_digest"] != b["content_digest"]


def test_multiple_cycles_have_distinct_digest_inputs():
    first = compute_handoff_digests("QA-0001", ["QA-0001-F01"], 1, "rev-001")
    second = compute_handoff_digests("QA-0001", ["QA-0001-F01"], 2, "rev-002")
    assert first["semantic_digest"] != second["semantic_digest"]
    assert first["content_digest"] != second["content_digest"]


def test_unknown_digest_version_is_rejected():
    from shared_core.digest import validate_digest_version

    assert validate_digest_version("v1") == "v1"
    with pytest.raises(ValueError, match="unsupported-digest-version"):
        validate_digest_version("v9")


def test_handoff_content_normalization_ignores_formatting_and_volatile_fields():
    from shared_core.digest import handoff_content_digest

    a = "- case_id: QA-1\n- created_at: t1\n- content_digest: old\n"
    b = "- case_id: QA-1  \r\n- created_at: t2\r\n- content_digest: new\r\n"
    assert handoff_content_digest(a) == handoff_content_digest(b)


def test_secret_values_are_rejected_from_digest_input():
    from shared_core.digest import content_digest

    with pytest.raises(ValueError, match="secret-in-digest-input"):
        content_digest({"token": "not-recorded"})


def test_content_only_handoff_change_is_detected(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0611")
    handoff = tmp_path / "QA-0611" / "handoff.md"
    handoff.write_text(
        handoff.read_text(encoding="utf-8").replace(
            "Awaiting author response or fix submission.",
            "本文だけを改変した不正な表示。",
        ),
        encoding="utf-8",
    )
    _touch(tmp_path, "src/fix.py")
    submission = {
        "finding_ids": ["QA-0611-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "prose evidence",
        "modified_files": ["src/fix.py"],
    }
    with pytest.raises(ValueError, match="does not match handoff content"):
        lifecycle.verify_submission(case_id="QA-0611", submission=submission, cycle=1)


def test_classify_evidence_ref_kinds():
    assert classify_evidence_ref("file:///tmp/x") == "file-uri"
    assert classify_evidence_ref("/abs/path.txt") == "absolute"
    assert classify_evidence_ref("evidence/out.txt") == "relative-path"
    assert classify_evidence_ref("notes.txt") == "relative-path"
    assert classify_evidence_ref("Added test and passed.") == "prose"


def test_verify_rejects_stale_semantic_digest(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0601")
    handoff = tmp_path / "QA-0601" / "handoff.md"
    text = handoff.read_text(encoding="utf-8")
    text = re.sub(r"(semantic_digest:\s*)\S+", r"\1deadbeef", text)
    handoff.write_text(text, encoding="utf-8")
    findings_before = (tmp_path / "QA-0601" / "findings.yaml").read_text(encoding="utf-8")
    _touch(tmp_path, "src/fix.py")
    submission = {
        "finding_ids": ["QA-0601-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "pytest prose evidence ok",
        "modified_files": ["src/fix.py"],
    }
    with pytest.raises(ValueError, match="semantic_digest is stale"):
        lifecycle.verify_submission(case_id="QA-0601", submission=submission, cycle=1)
    assert (tmp_path / "QA-0601" / "findings.yaml").read_text(encoding="utf-8") == findings_before


def test_verify_rejects_stale_content_digest(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0602")
    handoff = tmp_path / "QA-0602" / "handoff.md"
    text = handoff.read_text(encoding="utf-8")
    text = re.sub(r"(content_digest:\s*)\S+", r"\1cafebabe", text)
    handoff.write_text(text, encoding="utf-8")
    _touch(tmp_path, "src/fix.py")
    submission = {
        "finding_ids": ["QA-0602-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "pytest prose evidence ok",
        "modified_files": ["src/fix.py"],
    }
    with pytest.raises(ValueError, match="content_digest is stale"):
        lifecycle.verify_submission(case_id="QA-0602", submission=submission, cycle=1)


def test_verify_accepts_fresh_digest_golden(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0603")
    _touch(tmp_path, "src/fix.py")
    submission = {
        "finding_ids": ["QA-0603-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "prose non-path evidence",
        "modified_files": ["src/fix.py"],
    }
    res = lifecycle.verify_submission(case_id="QA-0603", submission=submission, cycle=1)
    assert res["status"] == "success"


def test_verify_rejects_absolute_and_file_uri_evidence(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0604")
    _touch(tmp_path, "src/fix.py")
    base = {
        "finding_ids": ["QA-0604-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "modified_files": ["src/fix.py"],
    }
    with pytest.raises(ValueError, match="absolute or file://"):
        lifecycle.verify_submission(
            case_id="QA-0604",
            submission={**base, "test_evidence": "/tmp/secret.log"},
            cycle=1,
        )
    with pytest.raises(ValueError, match="absolute or file://"):
        lifecycle.verify_submission(
            case_id="QA-0604",
            submission={**base, "test_evidence": "file:///tmp/secret.log"},
            cycle=1,
        )


def test_verify_accepts_existing_relative_evidence_path(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0605")
    _touch(tmp_path, "src/fix.py")
    ev = _touch(tmp_path, "evidence/pytest-out.txt")
    submission = {
        "finding_ids": ["QA-0605-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": ev,
        "modified_files": ["src/fix.py"],
    }
    assert lifecycle.verify_submission(case_id="QA-0605", submission=submission, cycle=1)["status"] == "success"


def test_verify_rejects_missing_relative_evidence_path(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0606")
    _touch(tmp_path, "src/fix.py")
    submission = {
        "finding_ids": ["QA-0606-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "evidence/missing-out.txt",
        "modified_files": ["src/fix.py"],
    }
    with pytest.raises(ValueError, match="test_evidence"):
        lifecycle.verify_submission(case_id="QA-0606", submission=submission, cycle=1)


def test_verify_rejects_empty_or_missing_modified_files(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0607")
    base = {
        "finding_ids": ["QA-0607-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "prose evidence",
    }
    with pytest.raises(ValueError, match="non-empty modified_files"):
        lifecycle.verify_submission(case_id="QA-0607", submission=base, cycle=1)
    with pytest.raises(ValueError, match="non-empty modified_files"):
        lifecycle.verify_submission(
            case_id="QA-0607",
            submission={**base, "modified_files": []},
            cycle=1,
        )


def test_verify_rejects_missing_modified_file_path(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0608")
    submission = {
        "finding_ids": ["QA-0608-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "prose evidence",
        "modified_files": ["src/does-not-exist.py"],
    }
    with pytest.raises(ValueError, match="Modified file .* does not exist"):
        lifecycle.verify_submission(case_id="QA-0608", submission=submission, cycle=1)


def test_verify_rejects_absolute_modified_file_outside_workspace(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0609")
    outside = tmp_path.parent / f"{tmp_path.name}-outside.py"
    outside.write_text("leak\n", encoding="utf-8")
    submission = {
        "finding_ids": ["QA-0609-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "prose evidence",
        "modified_files": [str(outside)],
    }
    with pytest.raises(ValueError, match="absolute paths are not accepted"):
        lifecycle.verify_submission(case_id="QA-0609", submission=submission, cycle=1)


def test_verify_rejects_dotdot_modified_file_outside_workspace(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0610")
    outside = tmp_path.parent / f"{tmp_path.name}-dotdot.py"
    outside.write_text("leak\n", encoding="utf-8")
    submission = {
        "finding_ids": ["QA-0610-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "prose evidence",
        "modified_files": [f"../{outside.name}"],
    }
    with pytest.raises(ValueError, match="outside the workspace"):
        lifecycle.verify_submission(case_id="QA-0610", submission=submission, cycle=1)


def test_verify_rejects_symlink_modified_file_outside_workspace(tmp_path):
    lifecycle = ReviewerLifecycle(qa_root=str(tmp_path), role="reviewer", workspace_root=str(tmp_path))
    _seed_case(lifecycle, "QA-0611")
    outside = tmp_path.parent / f"{tmp_path.name}-symlink-target.py"
    outside.write_text("leak\n", encoding="utf-8")
    link = tmp_path / "src" / "link.py"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside)
    submission = {
        "finding_ids": ["QA-0611-F01"],
        "base_revision": "rev-001",
        "status": "fix-submitted",
        "test_evidence": "prose evidence",
        "modified_files": ["src/link.py"],
    }
    with pytest.raises(ValueError, match="outside the workspace"):
        lifecycle.verify_submission(case_id="QA-0611", submission=submission, cycle=1)
