from __future__ import annotations

import tempfile
import unittest
import hashlib
from pathlib import Path
from unittest.mock import patch

from quality_loop import QualityLoop, QualityLoopError
from test_acceptance import finding
from test_quality_loop import complete_intake


def create_reviewed_case(loop: QualityLoop) -> dict:
    intake = complete_intake()
    intake["implementation_authorization"] = {
        "allowed": True,
        "finding_ids": ["F-001"],
        "allowed_targets": ["artifact.txt"],
    }
    created = loop.create_case(intake)
    return loop.review(
        "QMS-0001",
        {
            "operation_id": "op-review-001",
            "actor_id": "reviewer-001",
            "role": "reviewer",
            "invocation_id": "inv-reviewer-001",
            "previous_handoff_id": created["handoff"]["handoff_id"],
            "expected_case_revision": 1,
            "findings": [finding()],
            "evidence": [],
        },
    )


class RoleFirewallTest(unittest.TestCase):
    def test_create_case_requires_owner_and_safe_case_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            wrong_role = complete_intake()
            wrong_role["role"] = "reviewer"
            with self.assertRaises(QualityLoopError) as role_error:
                loop.create_case(wrong_role)
            self.assertEqual("role-not-allowed", role_error.exception.error_code)

            unsafe_id = complete_intake()
            unsafe_id["case_id"] = "../outside"
            with self.assertRaises(QualityLoopError) as id_error:
                loop.create_case(unsafe_id)
            self.assertEqual("invalid-case-id", id_error.exception.error_code)
            self.assertFalse((Path(temp_dir).parent / "outside").exists())

    def test_owner_identity_cannot_be_spoofed_at_create_or_adjudication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            spoofed_create = complete_intake()
            spoofed_create["actor_id"] = "implementer-001"
            with self.assertRaises(QualityLoopError) as create_error:
                loop.create_case(spoofed_create)
            self.assertEqual("owner-identity-mismatch", create_error.exception.error_code)

            created = loop.create_case(complete_intake())
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [],
                    "evidence": [],
                },
            )
            with self.assertRaises(QualityLoopError) as adjudication_error:
                loop.adjudicate(
                    "QMS-0001",
                    {
                        "operation_id": "op-adjudicate-spoofed",
                        "actor_id": "implementer-001",
                        "role": "owner",
                        "invocation_id": "inv-implementer-spoofed",
                        "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                        "expected_case_revision": 2,
                        "decision": "accepted",
                        "rationale": "不正な自己受入",
                        "confirm": True,
                    },
                )
            self.assertEqual("owner-identity-mismatch", adjudication_error.exception.error_code)

    def test_status_of_missing_case_root_does_not_create_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_root = Path(temp_dir) / "missing-root"
            loop = QualityLoop(missing_root)
            with self.assertRaises(QualityLoopError) as captured:
                loop.status("QMS-MISSING")
            self.assertEqual("case-not-found", captured.exception.error_code)
            self.assertFalse(missing_root.exists())

    def test_finding_without_evidence_or_unverified_reason_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            invalid_finding = finding()
            invalid_finding.pop("unverified_reason")
            invalid_finding.pop("required_evidence")
            with self.assertRaises(QualityLoopError) as captured:
                loop.review(
                    "QMS-0001",
                    {
                        "operation_id": "op-review-001",
                        "actor_id": "reviewer-001",
                        "role": "reviewer",
                        "invocation_id": "inv-reviewer-001",
                        "previous_handoff_id": created["handoff"]["handoff_id"],
                        "expected_case_revision": 1,
                        "findings": [invalid_finding],
                        "evidence": [],
                    },
                )
            self.assertEqual("finding-evidence-required", captured.exception.error_code)

            with self.assertRaises(QualityLoopError) as verification_error:
                loop._validate_verifications(
                    [{"finding_id": "F-001"}],
                    [
                        {
                            "finding_id": "F-001",
                            "result": "verified",
                            "rationale": "根拠なしの検証",
                            "evidence_refs": [],
                        }
                    ],
                )
            self.assertEqual(
                "verification-evidence-required", verification_error.exception.error_code
            )

    def test_implementer_self_close_is_rejected_without_state_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            reviewed = create_reviewed_case(loop)

            with self.assertRaises(QualityLoopError) as captured:
                loop.submit_response(
                    "QMS-0001",
                    {
                        "operation_id": "op-submit-001",
                        "actor_id": "implementer-001",
                        "role": "implementer",
                        "invocation_id": "inv-implementer-001",
                        "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                        "expected_case_revision": 2,
                        "case_status": "closed",
                        "changed_targets": [],
                        "responses": [
                            {
                                "finding_id": "F-001",
                                "disposition": "accepted",
                                "rationale": "自己クローズを試行",
                                "evidence_refs": [],
                            }
                        ],
                        "evidence": [],
                    },
                )

            self.assertEqual("forbidden-field", captured.exception.error_code)
            case = loop.store.load("QMS-0001")
            self.assertEqual(2, case["case_metadata"]["revision"])
            self.assertEqual("implementer-action", case["case_metadata"]["status"])

    def test_wrong_role_and_stale_revision_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            base_payload = {
                "operation_id": "op-review-001",
                "actor_id": "reviewer-001",
                "role": "implementer",
                "invocation_id": "inv-reviewer-001",
                "previous_handoff_id": created["handoff"]["handoff_id"],
                "expected_case_revision": 1,
                "findings": [],
                "evidence": [],
            }
            with self.assertRaises(QualityLoopError) as wrong_role:
                loop.review("QMS-0001", base_payload)
            self.assertEqual("role-not-allowed", wrong_role.exception.error_code)
            base_payload["role"] = "reviewer"
            base_payload["expected_case_revision"] = 0
            with self.assertRaises(QualityLoopError) as stale:
                loop.review("QMS-0001", base_payload)
            self.assertEqual("revision-conflict", stale.exception.error_code)
            self.assertEqual(1, loop.store.load("QMS-0001")["case_metadata"]["revision"])

    def test_duplicate_operation_returns_original_result_without_new_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            payload = {
                "operation_id": "op-review-001",
                "actor_id": "reviewer-001",
                "role": "reviewer",
                "invocation_id": "inv-reviewer-001",
                "previous_handoff_id": created["handoff"]["handoff_id"],
                "expected_case_revision": 1,
                "findings": [],
                "evidence": [],
            }
            first = loop.review("QMS-0001", payload)
            duplicate = loop.review("QMS-0001", payload)

            self.assertEqual("already-processed", duplicate["status"])
            self.assertFalse(duplicate["state_changed"])
            self.assertEqual(first["case_revision"], duplicate["case_revision"])
            self.assertEqual(2, loop.store.load("QMS-0001")["case_metadata"]["revision"])

    def test_unknown_finding_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            reviewed = create_reviewed_case(loop)
            with self.assertRaises(QualityLoopError) as captured:
                loop.submit_response(
                    "QMS-0001",
                    {
                        "operation_id": "op-submit-001",
                        "actor_id": "implementer-001",
                        "role": "implementer",
                        "invocation_id": "inv-implementer-001",
                        "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                        "expected_case_revision": 2,
                        "changed_targets": [],
                        "responses": [
                            {
                                "finding_id": "F-UNKNOWN",
                                "disposition": "accepted",
                                "rationale": "未知ID",
                                "evidence_refs": [],
                            }
                        ],
                        "evidence": [],
                    },
                )
            self.assertEqual("unknown-finding-id", captured.exception.error_code)
            self.assertEqual(2, loop.store.load("QMS-0001")["case_metadata"]["revision"])

    def test_tampered_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            reviewed = create_reviewed_case(loop)
            evidence_path = Path(temp_dir) / "QMS-0001" / "evidence" / "fix.txt"
            evidence_path.write_text("actual", encoding="utf-8")
            wrong_digest = hashlib.sha256(b"different").hexdigest()
            with self.assertRaises(QualityLoopError) as captured:
                loop.submit_response(
                    "QMS-0001",
                    {
                        "operation_id": "op-submit-001",
                        "actor_id": "implementer-001",
                        "role": "implementer",
                        "invocation_id": "inv-implementer-001",
                        "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                        "expected_case_revision": 2,
                        "changed_targets": ["artifact.txt"],
                        "responses": [
                            {
                                "finding_id": "F-001",
                                "disposition": "fix-submitted",
                                "rationale": "修正提出",
                                "evidence_refs": ["EV-001"],
                            }
                        ],
                        "evidence": [
                            {
                                "evidence_id": "EV-001",
                                "level": "observed",
                                "target_revision": "r2",
                                "method": "test",
                                "result": "passed",
                                "path": "evidence/fix.txt",
                                "sha256": wrong_digest,
                            }
                        ],
                    },
                )
            self.assertEqual("evidence-digest-mismatch", captured.exception.error_code)
            self.assertEqual(2, loop.store.load("QMS-0001")["case_metadata"]["revision"])

    def test_verify_rejects_undeclared_observed_change_without_state_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            reviewed = create_reviewed_case(loop)
            evidence_dir = Path(temp_dir) / "QMS-0001" / "evidence"
            fix_path = evidence_dir / "fix.txt"
            fix_path.write_text("passed\n", encoding="utf-8")
            submitted = loop.submit_response(
                "QMS-0001",
                {
                    "operation_id": "op-submit-001",
                    "actor_id": "implementer-001",
                    "role": "implementer",
                    "invocation_id": "inv-implementer-001",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "changed_targets": ["artifact.txt"],
                    "responses": [
                        {
                            "finding_id": "F-001",
                            "disposition": "fix-submitted",
                            "rationale": "対象を修正した",
                            "evidence_refs": ["EV-FIX"],
                        }
                    ],
                    "evidence": [
                        {
                            "evidence_id": "EV-FIX",
                            "level": "observed",
                            "target_revision": "r2",
                            "method": "修正確認",
                            "result": "passed",
                            "path": "evidence/fix.txt",
                            "sha256": hashlib.sha256(fix_path.read_bytes()).hexdigest(),
                        }
                    ],
                },
            )
            evidence = [
                {
                    "evidence_id": evidence_id,
                    "level": "observed",
                    "target_revision": revision,
                    "method": "有限manifest",
                    "result": "captured",
                    "summary": "観測結果",
                }
                for evidence_id, revision in (("EV-BEFORE", "r1"), ("EV-AFTER", "r2"))
            ]
            with self.assertRaises(QualityLoopError) as captured:
                loop.verify(
                    "QMS-0001",
                    {
                        "operation_id": "op-verify-001",
                        "actor_id": "reviewer-002",
                        "role": "reviewer",
                        "invocation_id": "inv-reviewer-002",
                        "previous_handoff_id": submitted["handoff"]["handoff_id"],
                        "expected_case_revision": 3,
                        "verifications": [
                            {
                                "finding_id": "F-001",
                                "result": "not-verified",
                                "rationale": "申告外変更がある",
                                "evidence_refs": ["EV-AFTER"],
                            }
                        ],
                        "new_findings": [],
                        "change_observation": {
                            "method": "finite-manifest",
                            "scope": ["artifact.txt", "extra.txt"],
                            "before_evidence_id": "EV-BEFORE",
                            "after_evidence_id": "EV-AFTER",
                            "observed_changed_targets": ["artifact.txt", "extra.txt"],
                            "limitations": [],
                        },
                        "evidence": evidence,
                    },
                )
            self.assertEqual("undeclared-change-detected", captured.exception.error_code)
            self.assertEqual(3, loop.store.load("QMS-0001")["case_metadata"]["revision"])

    def test_reviewer_cannot_register_missing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            with self.assertRaises(QualityLoopError) as captured:
                loop.review(
                    "QMS-0001",
                    {
                        "operation_id": "op-review-001",
                        "actor_id": "reviewer-001",
                        "role": "reviewer",
                        "invocation_id": "inv-reviewer-001",
                        "previous_handoff_id": created["handoff"]["handoff_id"],
                        "expected_case_revision": 1,
                        "findings": [finding()],
                        "evidence": [
                            {
                                "evidence_id": "EV-MISSING",
                                "level": "observed",
                                "target_revision": "r1",
                                "method": "inspection",
                                "result": "missing",
                                "path": "evidence/missing.txt",
                                "sha256": "0" * 64,
                            }
                        ],
                    },
                )
            self.assertEqual("evidence-not-found", captured.exception.error_code)
            self.assertEqual(1, loop.store.load("QMS-0001")["case_metadata"]["revision"])


class OwnerConfirmationTest(unittest.TestCase):
    def test_terminal_adjudication_supports_dry_run_and_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [],
                    "evidence": [],
                },
            )
            base = {
                "actor_id": "owner-001",
                "role": "owner",
                "invocation_id": "inv-owner-002",
                "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                "expected_case_revision": 2,
                "decision": "accepted",
                "rationale": "Findingなしの独立レビューを確認した",
                "conditions": [],
                "residual_risks": [],
            }
            preview_payload = dict(base)
            preview_payload.update(
                {"operation_id": "op-adjudicate-preview", "dry_run": True, "confirm": False}
            )

            preview = loop.adjudicate("QMS-0001", preview_payload)

            self.assertEqual("dry-run", preview["status"])
            self.assertFalse(preview["state_changed"])
            self.assertEqual(2, loop.store.load("QMS-0001")["case_metadata"]["revision"])

            final_payload = dict(base)
            final_payload.update(
                {"operation_id": "op-adjudicate-final", "dry_run": False, "confirm": True}
            )
            final = loop.adjudicate("QMS-0001", final_payload)
            self.assertEqual("terminal", final["handoff"]["status"])
            self.assertEqual(3, final["case_revision"])

    def test_held_case_can_be_resumed_by_owner_adjudication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [],
                    "evidence": [],
                },
            )
            held = loop.adjudicate(
                "QMS-0001",
                {
                    "operation_id": "op-hold-001",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-001",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "decision": "held",
                    "rationale": "判断材料が揃うまで保留する",
                },
            )
            self.assertEqual("owner", held["next_role"])
            self.assertEqual("adjudicate", held["next_action"])
            self.assertEqual("held", loop.store.load("QMS-0001")["case_metadata"]["status"])

            resumed = loop.adjudicate(
                "QMS-0001",
                {
                    "operation_id": "op-resume-001",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-002",
                    "previous_handoff_id": held["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "decision": "accepted",
                    "rationale": "判断材料を確認し受入可能と判断した",
                    "dry_run": False,
                    "confirm": True,
                },
            )
            self.assertEqual("terminal", resumed["handoff"]["status"])
            self.assertEqual(
                "accepted", loop.store.load("QMS-0001")["case_metadata"]["status"]
            )


class AtomicPersistenceTest(unittest.TestCase):
    def test_case_write_failure_keeps_previous_canonical_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            original_write = loop.store._atomic_write_json

            def fail_canonical_write(path: Path, payload: dict) -> None:
                if path.name == "case.json":
                    raise OSError("injected write failure")
                original_write(path, payload)

            with patch.object(loop.store, "_atomic_write_json", side_effect=fail_canonical_write):
                with self.assertRaises(QualityLoopError) as captured:
                    loop.review(
                        "QMS-0001",
                        {
                            "operation_id": "op-review-001",
                            "actor_id": "reviewer-001",
                            "role": "reviewer",
                            "invocation_id": "inv-reviewer-001",
                            "previous_handoff_id": created["handoff"]["handoff_id"],
                            "expected_case_revision": 1,
                            "findings": [],
                            "evidence": [],
                        },
                    )

            self.assertEqual("case-write-failed", captured.exception.error_code)
            self.assertEqual(1, loop.store.load("QMS-0001")["case_metadata"]["revision"])


if __name__ == "__main__":
    unittest.main()
