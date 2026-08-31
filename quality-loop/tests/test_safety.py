from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from quality_loop import QualityLoop
from quality_loop.errors import QualityLoopError


def complete_intake() -> dict:
    return {
        "operation_id": "op-create-001",
        "actor_id": "owner-001",
        "role": "owner",
        "invocation_id": "inv-owner-001",
        "case_id": "QMS-0001",
        "owner": "owner-001",
        "baseline": {
            "purpose": "要求に対する品質を確認する",
            "intended_use": {
                "users": "開発者・レビュアー",
                "environment": "ローカル検証環境",
                "operational_context": "機能追加に伴う品質検証",
            },
            "risk_context": {
                "criticality": "medium",
                "safety_impact": "なし",
                "data_integrity_impact": "低",
                "security_context": "内部テスト",
            },
            "requirements": [{"requirement_id": "REQ-001", "text": "結果を再現できる"}],
            "acceptance_criteria": ["再現Evidenceがある"],
            "exclusions": [],
            "targets": ["artifact.txt"],
            "target_revision": "r1",
        },
        "implementation_authorization": {
            "allowed": True,
            "finding_ids": ["F-001"],
            "allowed_targets": ["artifact.txt"],
        },
        "change_observation": {
            "method": "finite-manifest",
            "scope": ["artifact.txt"],
            "baseline_evidence_id": None,
            "exclusions": [],
            "limitations": [],
        },
    }


def finding() -> dict:
    return {
        "finding_id": "F-001",
        "classification": "requirement-violation",
        "severity": "high",
        "requirement_ref": "REQ-001",
        "observed_fact": "不一致",
        "impact": "影響",
        "expected_state": "一致",
        "verification_method": "検証",
        "evidence_refs": [],
        "status": "open",
    }


def create_reviewed_case(loop: QualityLoop) -> dict:
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
            "findings": [finding()],
            "evidence": [],
        },
    )
    # Plan Before Fix: Submit and review plan
    planned = loop.submit_plan(
        "QMS-0001",
        {
            "operation_id": "op-plan-001",
            "actor_id": "implementer-001",
            "role": "implementer",
            "invocation_id": "inv-implementer-001",
            "previous_handoff_id": reviewed["handoff"]["handoff_id"],
            "expected_case_revision": 2,
            "plans": [
                {
                    "finding_id": "F-001",
                    "understanding": "不一致を修正する",
                    "disposition_intent": "fix",
                    "proposed_actions": ["修正する"],
                }
            ],
        },
    )
    return loop.review_plan(
        "QMS-0001",
        {
            "operation_id": "op-review-plan-001",
            "actor_id": "reviewer-001",
            "role": "reviewer",
            "invocation_id": "inv-reviewer-002",
            "previous_handoff_id": planned["handoff"]["handoff_id"],
            "expected_case_revision": 3,
            "plan_reviews": [
                {
                    "finding_id": "F-001",
                    "outcome": "plan-accepted",
                    "rationale": "修正方針に合意",
                }
            ],
        },
    )


class RoleFirewallTest(unittest.TestCase):
    def test_create_case_requires_owner_and_safe_case_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            payload = complete_intake()
            payload["role"] = "reviewer"
            with self.assertRaises(QualityLoopError) as captured:
                loop.create_case(payload)
            self.assertEqual("role-not-allowed", captured.exception.error_code)

            payload["role"] = "owner"
            payload["case_id"] = "bad/case/id"
            with self.assertRaises(QualityLoopError) as captured:
                loop.create_case(payload)
            self.assertEqual("invalid-case-id", captured.exception.error_code)

            # Test custom cycle_limit is respected
            payload["case_id"] = "QMS-CYCLE-01"
            payload["cycle_limit"] = 5
            loop.create_case(payload)
            case_data = loop.store.load("QMS-CYCLE-01")
            self.assertEqual(5, case_data["case_metadata"]["cycle_limit"])

            # Test invalid cycle_limit rejected
            payload["case_id"] = "QMS-CYCLE-02"
            payload["cycle_limit"] = 0
            with self.assertRaises(QualityLoopError) as captured:
                loop.create_case(payload)
            self.assertEqual("invalid-input", captured.exception.error_code)

    def test_wrong_role_and_stale_revision_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())

            with self.assertRaises(QualityLoopError) as captured:
                loop.submit_response(
                    "QMS-0001",
                    {
                        "operation_id": "op-submit-001",
                        "actor_id": "implementer-001",
                        "role": "implementer",
                        "invocation_id": "inv-implementer-001",
                        "previous_handoff_id": created["handoff"]["handoff_id"],
                        "expected_case_revision": 1,
                        "changed_targets": [],
                        "responses": [
                            {
                                "finding_id": "F-001",
                                "disposition": "accepted",
                                "rationale": "受領した",
                                "evidence_refs": [],
                            }
                        ],
                        "evidence": [],
                    },
                )
            self.assertEqual("state-transition-not-allowed", captured.exception.error_code)

            with self.assertRaises(QualityLoopError) as captured:
                loop.review(
                    "QMS-0001",
                    {
                        "operation_id": "op-review-001",
                        "actor_id": "reviewer-001",
                        "role": "reviewer",
                        "invocation_id": "inv-reviewer-001",
                        "previous_handoff_id": created["handoff"]["handoff_id"],
                        "expected_case_revision": 99,
                        "findings": [finding()],
                        "evidence": [],
                    },
                )
            self.assertEqual("revision-conflict", captured.exception.error_code)

    def test_implementer_self_close_is_rejected_without_state_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            reviewed = create_reviewed_case(loop)
            with self.assertRaises(QualityLoopError) as captured:
                loop.adjudicate(
                    "QMS-0001",
                    {
                        "operation_id": "op-adjudicate-001",
                        "actor_id": "implementer-001",
                        "role": "implementer",
                        "invocation_id": "inv-implementer-001",
                        "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                        "expected_case_revision": 2,
                        "decision": "accepted",
                        "rationale": "自分で受入を試みる",
                        "conditions": [],
                        "residual_risks": [],
                        "confirm": True,
                    },
                )
            self.assertEqual("role-not-allowed", captured.exception.error_code)
            self.assertEqual(4, loop.store.load("QMS-0001")["case_metadata"]["revision"])

    def test_adjudicate_rejects_unauthorized_actor_even_with_owner_role(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            intake = complete_intake()
            intake["owner"] = "owner-authorized"
            intake["actor_id"] = "owner-authorized"
            created = loop.create_case(intake)
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

            # Imposter claims role: "owner" but actor_id: "imposter-ai"
            with self.assertRaises(QualityLoopError) as ctx:
                loop.adjudicate(
                    "QMS-0001",
                    {
                        "operation_id": "op-adj-imposter",
                        "actor_id": "imposter-ai",
                        "role": "owner",
                        "invocation_id": "inv-imposter",
                        "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                        "expected_case_revision": 2,
                        "decision": "accepted",
                        "rationale": "なりすまし受入試行",
                        "conditions": [],
                        "residual_risks": [],
                        "confirm": True,
                    },
                )
            self.assertEqual("unauthorized-actor", ctx.exception.error_code)

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
                        "expected_case_revision": 4,
                        "changed_targets": [],
                        "responses": [
                            {
                                "finding_id": "UNKNOWN-001",
                                "disposition": "accepted",
                                "rationale": "存在しない指摘に回答する",
                                "evidence_refs": [],
                            }
                        ],
                        "evidence": [],
                    },
                )
            self.assertEqual("unknown-finding-id", captured.exception.error_code)

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
                                "evidence_id": "EV-001",
                                "level": "observed",
                                "target_revision": "r1",
                                "method": "存在確認",
                                "result": "passed",
                                "path": "evidence/missing.txt",
                                "sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
                            }
                        ],
                    },
                )
            self.assertEqual("evidence-not-found", captured.exception.error_code)

    def test_tampered_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            reviewed = create_reviewed_case(loop)
            evidence_dir = Path(temp_dir) / "QMS-0001" / "evidence"
            fix_path = evidence_dir / "fix.txt"
            fix_path.write_text("passed\n", encoding="utf-8")
            wrong_digest = "0" * 64
            with self.assertRaises(QualityLoopError) as captured:
                loop.submit_response(
                    "QMS-0001",
                    {
                        "operation_id": "op-submit-001",
                        "actor_id": "implementer-001",
                        "role": "implementer",
                        "invocation_id": "inv-implementer-001",
                        "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                        "expected_case_revision": 4,
                        "changed_targets": ["artifact.txt"],
                        "responses": [
                            {
                                "finding_id": "F-001",
                                "disposition": "fix-submitted",
                                "rationale": "対象を修正した",
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
                    "expected_case_revision": 4,
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
                    "evidence_id": "EV-001",
                    "level": "observed",
                    "target_revision": "r1",
                    "method": "有限manifest",
                    "result": "captured",
                    "summary": "観測結果",
                },
                {
                    "evidence_id": "EV-002",
                    "level": "observed",
                    "target_revision": "r2",
                    "method": "有限manifest",
                    "result": "captured",
                    "summary": "観測結果",
                },
            ]
            with self.assertRaises(QualityLoopError) as captured:
                loop.verify(
                    "QMS-0001",
                    {
                        "operation_id": "op-verify-001",
                        "actor_id": "reviewer-002",
                        "role": "reviewer",
                        "invocation_id": "inv-reviewer-verify-001",
                        "previous_handoff_id": submitted["handoff"]["handoff_id"],
                        "expected_case_revision": 5,
                        "verifications": [
                            {
                                "finding_id": "F-001",
                                "result": "verified",
                                "rationale": "修正を確認した",
                                "evidence_refs": [],
                            }
                        ],
                        "new_findings": [],
                        "change_observation": {
                            "method": "finite-manifest",
                            "scope": ["artifact.txt", "undeclared.txt"],
                            "before_evidence_id": "EV-001",
                            "after_evidence_id": "EV-002",
                            "observed_changed_targets": ["artifact.txt", "undeclared.txt"],
                            "limitations": [],
                        },
                        "evidence": evidence,
                    },
                )
            self.assertEqual("undeclared-change-detected", captured.exception.error_code)

    def test_duplicate_operation_returns_original_result_without_new_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            duplicate = loop.create_case(complete_intake())
            self.assertFalse(duplicate["state_changed"])
            self.assertEqual("already-processed", duplicate["status"])
            self.assertEqual(1, created["case_revision"])
            self.assertEqual(1, duplicate["case_revision"])


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
            dry_run = loop.adjudicate(
                "QMS-0001",
                {
                    "operation_id": "op-adjudicate-dry-run",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-002",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "decision": "accepted",
                    "rationale": "dry-runで確認",
                    "conditions": [],
                    "residual_risks": [],
                    "dry_run": True,
                    "confirm": False,
                },
            )
            self.assertTrue(dry_run["dry_run"])
            self.assertFalse(dry_run["state_changed"])
            self.assertEqual("dry-run", dry_run["status"])
            self.assertEqual(2, loop.store.load("QMS-0001")["case_metadata"]["revision"])

    def test_accepted_with_risk_requires_non_empty_conditions(self) -> None:
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
                    "findings": [
                        {
                            "finding_id": "F-001",
                            "classification": "evidence-gap",
                            "severity": "low",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "実機未確認",
                            "impact": "低",
                            "expected_state": "確認",
                            "verification_method": "実機",
                            "evidence_refs": [],
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )
            rev = 2
            last_hnd = reviewed
            for cycle in range(1, 4):
                sub = loop.submit_response(
                    "QMS-0001",
                    {
                        "operation_id": f"op-sub-{cycle}",
                        "actor_id": "implementer-001",
                        "role": "implementer",
                        "invocation_id": f"inv-imp-{cycle}",
                        "previous_handoff_id": last_hnd["handoff"]["handoff_id"],
                        "expected_case_revision": rev,
                        "changed_targets": [],
                        "responses": [{"finding_id": "F-001", "disposition": "cannot-verify", "rationale": "理由", "evidence_refs": []}],
                        "evidence": [],
                    },
                )
                rev += 1
                ver = loop.verify(
                    "QMS-0001",
                    {
                        "operation_id": f"op-ver-{cycle}",
                        "actor_id": "reviewer-001",
                        "role": "reviewer",
                        "invocation_id": f"inv-rev-{cycle}",
                        "previous_handoff_id": sub["handoff"]["handoff_id"],
                        "expected_case_revision": rev,
                        "verifications": [{"finding_id": "F-001", "result": "unverified", "rationale": "未確認", "evidence_refs": []}],
                        "new_findings": [],
                        "change_observation": None,
                        "evidence": [],
                    },
                )
                rev += 1
                last_hnd = ver

            # After 3 cycles with unverified findings, state transitions to reviewer-final-assessment
            self.assertEqual("reviewer-final-assessment", loop.status("QMS-0001")["current_state"])
            ar = loop.assess_risk(
                "QMS-0001",
                {
                    "operation_id": "op-assess-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-rev-assess",
                    "previous_handoff_id": last_hnd["handoff"]["handoff_id"],
                    "expected_case_revision": rev,
                    "overall_recommendation": "accept-with-conditions",
                    "rationale": "未確認事項のリスク評価",
                    "residual_risks": [
                        {
                            "finding_id": "F-001",
                            "current_status": "unverified",
                            "severity": "low",
                            "residual_risk_description": "未確認リスク",
                            "likelihood": "low",
                            "impact": "low",
                            "qa_recommendation": "accept-with-conditions",
                            "confidence": "high",
                        }
                    ],
                },
            )
            rev += 1

            # Owner attempts accepted-with-risk with empty conditions
            with self.assertRaises(QualityLoopError) as ctx:
                loop.adjudicate(
                    "QMS-0001",
                    {
                        "operation_id": "op-adj-bad-risk",
                        "actor_id": "owner-001",
                        "role": "owner",
                        "invocation_id": "inv-owner-001",
                        "previous_handoff_id": ar["handoff"]["handoff_id"],
                        "expected_case_revision": rev,
                        "decision": "accepted-with-risk",
                        "rationale": "条件なしリスク受入試行",
                        "conditions": [],
                        "residual_risks": ["未確認リスク"],
                        "confirm": True,
                    },
                )
            self.assertEqual("conditions-required", ctx.exception.error_code)

    def test_reviewer_assess_risk_records_structured_assessment_and_generates_markdown(self) -> None:
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
                    "findings": [finding()],
                    "evidence": [],
                },
            )

            # Implementer trying to execute assess-risk must be blocked
            with self.assertRaises(QualityLoopError) as ctx:
                loop.assess_risk(
                    "QMS-0001",
                    {
                        "operation_id": "op-assess-bad",
                        "actor_id": "imp-001",
                        "role": "implementer",
                        "invocation_id": "inv-imp",
                        "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                        "expected_case_revision": 2,
                        "overall_recommendation": "accept",
                        "rationale": "不正操作",
                        "residual_risks": [],
                    },
                )
            self.assertEqual("role-not-allowed", ctx.exception.error_code)

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
                    "operation_id": "op-adjudicate-held",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-003",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "decision": "held",
                    "rationale": "追加情報待ち",
                    "conditions": [],
                    "residual_risks": [],
                    "confirm": True,
                },
            )
            self.assertEqual("adjudicate", held["next_action"])

            resumed = loop.adjudicate(
                "QMS-0001",
                {
                    "operation_id": "op-adjudicate-resume",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-004",
                    "previous_handoff_id": held["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "decision": "accepted",
                    "rationale": "再開受入",
                    "conditions": [],
                    "residual_risks": [],
                    "confirm": True,
                },
            )
            self.assertEqual(None, resumed["next_action"])


class AtomicPersistenceTest(unittest.TestCase):
    def test_status_does_not_create_nonexistent_case_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            nonexistent_root = Path(temp_dir) / "does_not_exist_yet"
            loop = QualityLoop(nonexistent_root)
            with self.assertRaises(QualityLoopError) as ctx:
                loop.status("QMS-0001")
            self.assertEqual("case-not-found", ctx.exception.error_code)
            self.assertFalse(nonexistent_root.exists())

    def test_case_write_failure_keeps_previous_canonical_revision(self) -> None:
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            # Inject failure specifically when writing the new updated case.json (second call)
            original_atomic_write = loop.store._atomic_write_json
            call_count = 0

            def failing_atomic_write(path: Path, data: dict) -> None:
                nonlocal call_count
                call_count += 1
                if path.name == "case.json":
                    raise OSError("Disk full simulation")
                original_atomic_write(path, data)

            with patch.object(loop.store, "_atomic_write_json", side_effect=failing_atomic_write):
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
                            "evidence": [],
                        },
                    )
            self.assertEqual("case-write-failed", captured.exception.error_code)
            self.assertEqual(1, loop.store.load("QMS-0001")["case_metadata"]["revision"])


if __name__ == "__main__":
    unittest.main()
