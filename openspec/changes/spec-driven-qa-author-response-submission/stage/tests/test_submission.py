from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

STAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STAGE))
CANONICAL = STAGE / "fixtures" / "valid"

from spec_driven_qa_author_response_submission.submission import (  # noqa: E402
    validate_submission,
    write_author_response,
    write_submission,
)
from spec_driven_qa_author_response_submission.shared_core_adapter import load_shared_core  # noqa: E402


HANDOFF = """# QA Review Handoff Contract

- schema_version: \"1.2\"
- digest_version: \"v1\"
- case_id: QA-9001
- cycle: 3
- case_revision: 3
- content_digest: 365eacb83e8647adc4c1e2fc6ff4cbc4d4675190097e814ad57f11ac0c03183f
- semantic_digest: be211554cbc4332e46f262772f8ecc07464f35ede7219cf5a78c168cf238a9c7
- created_at: 2026-08-26T00:00:00+09:00
- origin_role: reviewer
- implementation_permission: scoped
- open_finding_ids: [\"QA-9001-F01\"]

## Active Open Findings

- `QA-9001-F01`: Awaiting author response or fix submission.
"""


def valid_submission() -> dict:
    return {
        "submission_id": "submission-001",
        "case_id": "QA-9001",
        "contract_version": "1.2",
        "base_revision": 3,
        "expected_semantic_digest": "be211554cbc4332e46f262772f8ecc07464f35ede7219cf5a78c168cf238a9c7",
        "expected_content_digest": "365eacb83e8647adc4c1e2fc6ff4cbc4d4675190097e814ad57f11ac0c03183f",
        "responses": {
            "QA-9001-F01": {
                "disposition": "accepted",
                "justification": "仕様上の指摘を受け入れる。",
            }
        },
        "evidence": ["観測結果を記録した"],
        "modified_files": [],
    }


def test_accepted_submission_is_valid():
    assert validate_submission(valid_submission(), HANDOFF, Path.cwd(), CANONICAL) == []


def test_shared_core_adapter_resolves_canonical_digest():
    content_digest, allowed = load_shared_core()
    assert content_digest({"case": "QA-9001"})
    assert allowed("author", "submit") is True
    assert allowed("author", "close") is False


@pytest.mark.parametrize("disposition", ["accepted", "fix-submitted", "rejected-with-evidence", "deferred", "risk-accepted"])
def test_allowed_dispositions_are_accepted(disposition):
    submission = valid_submission()
    submission["responses"]["QA-9001-F01"]["disposition"] = disposition
    if disposition == "fix-submitted":
        submission["result_revision"] = 4
        submission["modified_files"] = ["openspec/specs/spec-driven-qa/spec.md"]
    assert not any("invalid Disposition" in error for error in validate_submission(submission, HANDOFF, Path.cwd(), CANONICAL))


def test_unknown_finding_is_rejected():
    submission = valid_submission()
    submission["responses"]["QA-9001-F99"] = submission["responses"].pop("QA-9001-F01")
    assert any("unknown Finding" in error for error in validate_submission(submission, HANDOFF, Path.cwd(), CANONICAL))


def test_finding_in_prose_is_not_an_allowed_finding():
    submission = valid_submission()
    prose_handoff = HANDOFF.replace("対象Finding: QA-9001-F01", "説明文: See also QA-9001-F99\n対象Finding: QA-9001-F01")
    assert any("unknown Finding" in error for error in validate_submission({**submission, "responses": {"QA-9001-F99": submission["responses"]["QA-9001-F01"]}}, prose_handoff, Path.cwd(), CANONICAL))


@pytest.mark.parametrize("disposition", ["closed", "fixed-and-verified"])
def test_author_cannot_self_close(disposition):
    submission = valid_submission()
    submission["responses"]["QA-9001-F01"]["disposition"] = disposition
    assert any("self-close" in error for error in validate_submission(submission, HANDOFF, Path.cwd(), CANONICAL))


def test_stale_digest_is_rejected():
    submission = valid_submission()
    submission["expected_content_digest"] = "stale"
    assert any("content_digest" in error for error in validate_submission(submission, HANDOFF, Path.cwd(), CANONICAL))


def test_content_only_handoff_change_is_rejected():
    changed = HANDOFF.replace(
        "Awaiting author response or fix submission.",
        "本文だけを改変した不正な表示。",
    )
    errors = validate_submission(valid_submission(), changed, Path.cwd(), CANONICAL)
    assert any("does not match handoff content" in error for error in errors)


def test_legacy_equivalent_digests_are_rejected():
    legacy_digest = "a" * 64
    legacy = HANDOFF.replace(
        "be211554cbc4332e46f262772f8ecc07464f35ede7219cf5a78c168cf238a9c7",
        legacy_digest,
    ).replace(
        "365eacb83e8647adc4c1e2fc6ff4cbc4d4675190097e814ad57f11ac0c03183f",
        legacy_digest,
    )
    submission = valid_submission()
    submission["expected_semantic_digest"] = legacy_digest
    submission["expected_content_digest"] = legacy_digest
    errors = validate_submission(submission, legacy, Path.cwd(), CANONICAL)
    assert any("legacy equivalent" in error for error in errors)


def test_reviewer_owned_fields_are_rejected():
    submission = valid_submission()
    submission["closure"] = "closed"
    assert any("Reviewer-owned field" in error for error in validate_submission(submission, HANDOFF, Path.cwd(), CANONICAL))


def test_filesystem_write_allowlist_rejects_reviewer_paths(tmp_path: Path):
    from spec_driven_qa_author_response_submission.submission import author_write_path_allowed

    assert author_write_path_allowed(tmp_path / "cycles/cycle-01-author-response.md", tmp_path)
    assert author_write_path_allowed(tmp_path / "cycles/cycle-01-submission.json", tmp_path)
    for name in ["review.md", "findings.yaml", "handoff.md", "events.jsonl"]:
        assert not author_write_path_allowed(tmp_path / name, tmp_path)


def test_file_uri_evidence_is_rejected():
    submission = valid_submission()
    submission["evidence"] = ["file:///tmp/evidence.txt"]
    assert any("file://" in error for error in validate_submission(submission, HANDOFF, Path.cwd(), CANONICAL))


def test_missing_evidence_path_is_rejected(tmp_path: Path):
    submission = valid_submission()
    submission["evidence"] = ["evidence/missing.txt"]
    assert any("evidence does not exist" in error for error in validate_submission(submission, HANDOFF, tmp_path, CANONICAL))


def test_absolute_and_workspace_escape_are_rejected(tmp_path: Path):
    submission = valid_submission()
    submission["evidence"] = ["/tmp/outside.txt", "../outside.txt"]
    errors = validate_submission(submission, HANDOFF, tmp_path, CANONICAL)
    assert any("absolute paths" in error for error in errors)
    assert any("outside workspace" in error for error in errors)


def test_fix_submission_requires_existing_modified_file(tmp_path: Path):
    submission = valid_submission()
    submission["responses"]["QA-9001-F01"]["disposition"] = "fix-submitted"
    submission["result_revision"] = 4
    submission["modified_files"] = ["src/missing.py"]
    assert any("modified file does not exist" in error for error in validate_submission(submission, HANDOFF, tmp_path, CANONICAL))


def test_base_revision_must_match_handoff():
    submission = valid_submission()
    submission["base_revision"] = 99
    assert any("base_revision does not match" in error for error in validate_submission(submission, HANDOFF, Path.cwd(), CANONICAL))


def test_canonical_case_dir_is_required():
    assert any("canonical_case_dir is required" in error for error in validate_submission(valid_submission(), HANDOFF, Path.cwd()))


def test_closed_canonical_findings_are_excluded_from_reviewer_digest(tmp_path: Path):
    case_dir = tmp_path / "QA-9001"
    case_dir.mkdir()
    (case_dir / "findings.yaml").write_text(
        "findings:\n"
        "  - id: QA-9001-F01\n"
        "    status: open\n"
        "  - id: QA-9001-F02\n"
        "    status: fixed-and-verified\n",
        encoding="utf-8",
    )
    assert validate_submission(valid_submission(), HANDOFF, tmp_path, case_dir) == []


def test_symlink_escape_is_rejected(tmp_path: Path):
    outside = tmp_path.parent / "outside-author-test.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = tmp_path / "link.txt"
    link.symlink_to(outside)
    submission = valid_submission()
    submission["responses"]["QA-9001-F01"]["disposition"] = "fix-submitted"
    submission["result_revision"] = 4
    submission["modified_files"] = ["link.txt"]
    assert any("outside workspace" in error for error in validate_submission(submission, HANDOFF, tmp_path, CANONICAL))


def test_submission_and_response_are_written_to_author_paths(tmp_path: Path):
    case = tmp_path / "QA-9001"
    response_path = write_author_response(case, 1, valid_submission())
    submission_path = write_submission(case, 1, valid_submission())
    assert response_path.name == "cycle-01-author-response.md"
    assert submission_path.name == "cycle-01-submission.json"
    assert json.loads(submission_path.read_text(encoding="utf-8"))["submission_id"] == "submission-001"
    assert not (case / "review.md").exists()


def test_cli_save_wires_public_submission_path(tmp_path: Path):
    from spec_driven_qa_author_response_submission.launcher import main

    case = tmp_path / "QA-9001"
    case.mkdir()
    (case / "handoff.md").write_text(HANDOFF, encoding="utf-8")
    (case / "findings.yaml").write_text("findings:\n  - id: QA-9001-F01\n    status: open\n", encoding="utf-8")
    submission_path = tmp_path / "submission.json"
    submission_path.write_text(json.dumps(valid_submission()), encoding="utf-8")
    assert main([str(case / "handoff.md"), str(submission_path), "--workspace", str(tmp_path), "--save"]) == 0
    assert (case / "cycles/cycle-01-author-response.md").exists()
    assert (case / "cycles/cycle-01-submission.json").exists()


def test_duplicate_submission_is_rejected(tmp_path: Path):
    case = tmp_path / "QA-9001"
    write_submission(case, 1, valid_submission())
    with pytest.raises(FileExistsError):
        write_submission(case, 1, valid_submission())
