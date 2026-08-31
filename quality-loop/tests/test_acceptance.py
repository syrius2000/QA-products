from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from quality_loop import QualityLoop, QualityLoopError
from test_quality_loop import complete_intake


def finding(
    finding_id: str = "F-001",
    *,
    classification: str = "requirement-violation",
    status: str = "open",
) -> dict:
    return {
        "finding_id": finding_id,
        "classification": classification,
        "severity": "low",
        "requirement_ref": "REQ-001",
        "observed_fact": "確認対象の事実",
        "impact": "要求達成を判断できない",
        "expected_state": "第三者が要求達成を確認できる",
        "verification_method": "独立確認する",
        "evidence_refs": [],
        "status": status,
    }


class ProportionalReviewAcceptanceTest(unittest.TestCase):
    def test_improvement_proposal_does_not_force_implementer_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())

            result = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        finding("I-001", classification="improvement-proposal")
                    ],
                    "evidence": [],
                },
            )

            self.assertEqual("owner", result["next_role"])
            self.assertEqual("adjudicate", result["next_action"])
            self.assertEqual(
                "owner-adjudication",
                loop.store.load("QMS-0001")["case_metadata"]["status"],
            )


class BaselineControlAcceptanceTest(unittest.TestCase):
    def test_implementer_baseline_change_request_routes_to_owner_without_change(self) -> None:
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
            original_baseline = loop.store.load("QMS-0001")["baseline"]

            result = loop.submit_response(
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
                            "finding_id": "F-001",
                            "disposition": "baseline-change-requested",
                            "rationale": "要求解釈をOwnerへ確認したい",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )

            self.assertEqual("owner", result["next_role"])
            self.assertEqual("adjudicate", result["next_action"])
            case = loop.store.load("QMS-0001")
            self.assertEqual(original_baseline, case["baseline"])
            self.assertEqual("owner-adjudication", case["case_metadata"]["status"])

    def test_owner_baseline_update_requires_reviewer_rereview(self) -> None:
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
            requested = loop.submit_response(
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
                            "finding_id": "F-001",
                            "disposition": "baseline-change-requested",
                            "rationale": "要求解釈をOwnerへ確認したい",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )
            new_baseline = complete_intake()["baseline"]
            new_baseline["target_revision"] = "r2"
            new_baseline["acceptance_criteria"] = ["r2の再現Evidenceがある"]

            result = loop.adjudicate(
                "QMS-0001",
                {
                    "operation_id": "op-adjudicate-001",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-002",
                    "previous_handoff_id": requested["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "decision": "rework-requested",
                    "rationale": "基準を明確化し再レビューする",
                    "conditions": [],
                    "residual_risks": [],
                    "baseline_update": new_baseline,
                },
            )

            self.assertEqual("reviewer", result["next_role"])
            self.assertEqual("review", result["next_action"])
            case = loop.store.load("QMS-0001")
            self.assertEqual("r2", case["baseline"]["target_revision"])
            self.assertEqual("requires-rereview", case["findings"][0]["status"])


class EvidenceGapAndCycleLimitAcceptanceTest(unittest.TestCase):
    def test_unverified_stays_distinct_and_third_cycle_routes_to_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            handoff = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [finding(classification="evidence-gap")],
                    "evidence": [],
                },
            )
            revision = 2
            for cycle in range(1, 4):
                submitted = loop.submit_response(
                    "QMS-0001",
                    {
                        "operation_id": f"op-submit-{cycle}",
                        "actor_id": "implementer-001",
                        "role": "implementer",
                        "invocation_id": f"inv-implementer-{cycle}",
                        "previous_handoff_id": handoff["handoff"]["handoff_id"],
                        "expected_case_revision": revision,
                        "changed_targets": [],
                        "responses": [
                            {
                                "finding_id": "F-001",
                                "disposition": "cannot-verify",
                                "rationale": "必要な外部環境がない",
                                "evidence_refs": [],
                            }
                        ],
                        "evidence": [],
                    },
                )
                revision += 1
                handoff = loop.verify(
                    "QMS-0001",
                    {
                        "operation_id": f"op-verify-{cycle}",
                        "actor_id": "reviewer-002",
                        "role": "reviewer",
                        "invocation_id": f"inv-reviewer-verify-{cycle}",
                        "previous_handoff_id": submitted["handoff"]["handoff_id"],
                        "expected_case_revision": revision,
                        "verifications": [
                            {
                                "finding_id": "F-001",
                                "result": "unverified",
                                "rationale": "外部環境がなく成否を確認できない",
                                "evidence_refs": [],
                            }
                        ],
                        "new_findings": [],
                        "change_observation": None,
                        "evidence": [],
                    },
                )
                revision += 1
                if cycle < 3:
                    self.assertEqual("implementer", handoff["next_role"])
                else:
                    self.assertEqual("reviewer", handoff["next_role"])
                    self.assertEqual("assess-risk", handoff["next_action"])

            case = loop.store.load("QMS-0001")
            self.assertEqual("unverified", case["findings"][0]["status"])
            self.assertEqual(3, case["case_metadata"]["cycle_count"])
            self.assertEqual("reviewer-final-assessment", case["case_metadata"]["status"])

            assessed = loop.assess_risk(
                "QMS-0001",
                {
                    "operation_id": "op-assess-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-assess-001",
                    "previous_handoff_id": handoff["handoff"]["handoff_id"],
                    "expected_case_revision": revision,
                    "overall_recommendation": "accept-with-conditions",
                    "rationale": "外部環境不足による未確認であり、ステージングでの追加テストを推奨",
                    "residual_risks": [
                        {
                            "finding_id": "F-001",
                            "current_status": "unverified",
                            "severity": "low",
                            "residual_risk_description": "外部環境未検証リスク",
                            "likelihood": "low",
                            "impact": "medium",
                            "qa_recommendation": "accept-with-conditions",
                            "confidence": "high",
                        }
                    ],
                },
            )
            revision += 1
            self.assertEqual("owner-adjudication", loop.status("QMS-0001")["current_state"])

            accepted = loop.adjudicate(
                "QMS-0001",
                {
                    "operation_id": "op-adjudicate-001",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-002",
                    "previous_handoff_id": assessed["handoff"]["handoff_id"],
                    "expected_case_revision": revision,
                    "decision": "accepted-with-risk",
                    "rationale": "外部環境の不備によるunverifiedを受容する",
                    "conditions": ["別工程で外部環境の検証を行うこと"],
                    "residual_risks": ["外部環境未検証リスク"],
                    "confirm": True,
                },
            )
            self.assertEqual("terminal", accepted["handoff"]["status"])
            self.assertEqual(
                "accepted-with-risk",
                loop.store.load("QMS-0001")["case_metadata"]["status"],
            )

    def test_owner_must_explicitly_authorize_cycles_after_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            handoff = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [finding(classification="evidence-gap")],
                    "evidence": [],
                },
            )
            revision = 2
            for cycle in range(1, 4):
                submitted = loop.submit_response(
                    "QMS-0001",
                    {
                        "operation_id": f"op-submit-{cycle}",
                        "actor_id": "implementer-001",
                        "role": "implementer",
                        "invocation_id": f"inv-implementer-{cycle}",
                        "previous_handoff_id": handoff["handoff"]["handoff_id"],
                        "expected_case_revision": revision,
                        "changed_targets": [],
                        "responses": [
                            {
                                "finding_id": "F-001",
                                "disposition": "cannot-verify",
                                "rationale": "必要な外部環境がない",
                                "evidence_refs": [],
                            }
                        ],
                        "evidence": [],
                    },
                )
                revision += 1
                handoff = loop.verify(
                    "QMS-0001",
                    {
                        "operation_id": f"op-verify-{cycle}",
                        "actor_id": "reviewer-002",
                        "role": "reviewer",
                        "invocation_id": f"inv-reviewer-verify-{cycle}",
                        "previous_handoff_id": submitted["handoff"]["handoff_id"],
                        "expected_case_revision": revision,
                        "verifications": [
                            {
                                "finding_id": "F-001",
                                "result": "unverified",
                                "rationale": "外部環境がない",
                                "evidence_refs": [],
                            }
                        ],
                        "new_findings": [],
                        "change_observation": None,
                        "evidence": [],
                    },
                )
                revision += 1

            # After 3 cycles with unverified findings, state transitions to reviewer-final-assessment
            self.assertEqual("reviewer-final-assessment", loop.status("QMS-0001")["current_state"])
            ar = loop.assess_risk(
                "QMS-0001",
                {
                    "operation_id": "op-assess-002",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-assess-002",
                    "previous_handoff_id": handoff["handoff"]["handoff_id"],
                    "expected_case_revision": revision,
                    "overall_recommendation": "require-remediation",
                    "rationale": "外部環境での追加作業が必要",
                    "residual_risks": [
                        {
                            "finding_id": "F-001",
                            "current_status": "unverified",
                            "severity": "low",
                            "residual_risk_description": "外部環境未検証リスク",
                            "likelihood": "high",
                            "impact": "medium",
                            "qa_recommendation": "require-remediation",
                            "confidence": "high",
                        }
                    ],
                },
            )
            revision += 1

            base = {
                "actor_id": "owner-001",
                "role": "owner",
                "invocation_id": "inv-owner-002",
                "previous_handoff_id": ar["handoff"]["handoff_id"],
                "expected_case_revision": revision,
                "decision": "rework-requested",
                "rationale": "外部環境で追加確認する",
            }
            with self.assertRaises(QualityLoopError) as captured:
                loop.adjudicate("QMS-0001", {**base, "operation_id": "op-rework-denied"})
            self.assertEqual("additional-cycles-required", captured.exception.error_code)

            resumed = loop.adjudicate(
                "QMS-0001",
                {
                    **base,
                    "operation_id": "op-rework-allowed",
                    "additional_cycles": 2,
                    "implementation_authorization": {
                        "allowed": True,
                        "finding_ids": ["F-001"],
                        "allowed_targets": ["artifact.txt"],
                    },
                },
            )
            self.assertEqual("implementer", resumed["next_role"])
            case = loop.store.load("QMS-0001")
            self.assertEqual(5, case["case_metadata"]["cycle_limit"])
            self.assertEqual(revision + 1, case["case_metadata"]["revision"])
            self.assertTrue(case["implementation_authorization"]["allowed"])


class RebuttalAndRegressionAcceptanceTest(unittest.TestCase):
    def test_evidence_rebuttal_is_verified_and_regression_gets_new_finding(self) -> None:
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
            submitted = loop.submit_response(
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
                            "finding_id": "F-001",
                            "disposition": "disagreed-with-evidence",
                            "rationale": "既存仕様により要求を満たしている",
                            "evidence_refs": ["EV-REBUTTAL"],
                        }
                    ],
                    "evidence": [
                        {
                            "evidence_id": "EV-REBUTTAL",
                            "level": "observed",
                            "target_revision": "r1",
                            "method": "仕様記載の直接確認",
                            "result": "requirement-satisfied",
                            "summary": "REQ-001に対応する再現条件を確認した",
                        }
                    ],
                },
            )

            result = loop.verify(
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
                            "result": "verified",
                            "rationale": "反証Evidenceを独立確認した",
                            "evidence_refs": ["EV-REBUTTAL"],
                        }
                    ],
                    "new_findings": [finding("F-002")],
                    "change_observation": None,
                    "evidence": [],
                },
            )

            self.assertEqual("implementer", result["next_role"])
            case = loop.store.load("QMS-0001")
            states = {item["finding_id"]: item["status"] for item in case["findings"]}
            self.assertEqual("verified", states["F-001"])
            self.assertEqual("open", states["F-002"])

    def test_early_final_risk_assessment_at_cycle_1_without_forcing_3_cycles(self) -> None:
        """Phase 3: 限界便益が小さい場合、3サイクル反復を待たずにCycle 1で早期Final Risk Assessmentへ移行可能"""
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
                    "findings": [finding("F-001", classification="evidence-gap")],
                    "evidence": [],
                },
            )
            submitted = loop.submit_response(
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
                            "finding_id": "F-001",
                            "disposition": "cannot-verify",
                            "rationale": "外部環境の制約により検証不能",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )

            # Cycle 1 verification with early_risk_assessment=True
            verified = loop.verify(
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
                            "result": "unverified",
                            "rationale": "環境制約を確認したため、これ以上の修正ループは不要と判断",
                            "evidence_refs": [],
                        }
                    ],
                    "new_findings": [],
                    "change_observation": None,
                    "evidence": [],
                    "early_risk_assessment": True,
                    "early_risk_rationale": "外部環境制約によりこれ以上の修正ループは費用対効果が低く、Owner裁定が妥当",
                },
            )

            # Transitions directly to reviewer-final-assessment at cycle 1
            self.assertEqual("reviewer", verified["next_role"])
            self.assertEqual("assess-risk", verified["next_action"])
            self.assertEqual("reviewer-final-assessment", loop.status("QMS-0001")["current_state"])

    def test_early_final_risk_assessment_rejects_empty_rationale(self) -> None:
        """Phase 6: early_risk_assessment=True で early_risk_rationale が空の場合は拒否される"""
        from quality_loop.errors import QualityLoopError

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
                    "findings": [finding("F-001", classification="evidence-gap")],
                    "evidence": [],
                },
            )
            submitted = loop.submit_response(
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
                            "finding_id": "F-001",
                            "disposition": "cannot-verify",
                            "rationale": "外部環境の制約により検証不能",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )

            with self.assertRaises(QualityLoopError) as ctx:
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
                                "result": "unverified",
                                "rationale": "環境制約を確認",
                                "evidence_refs": [],
                            }
                        ],
                        "new_findings": [],
                        "change_observation": None,
                        "evidence": [],
                        "early_risk_assessment": True,
                        "early_risk_rationale": "",
                    },
                )
            self.assertEqual("invalid-input", ctx.exception.error_code)

    def test_early_final_risk_assessment_rejects_unresolved_critical_finding(self) -> None:
        """Phase 6: 未解決のCritical指摘が存在する場合、early_risk_assessmentは拒否される"""
        from quality_loop.errors import QualityLoopError

        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            intake = complete_intake()
            intake["implementation_authorization"] = {
                "allowed": True,
                "finding_ids": ["F-001"],
                "allowed_targets": ["artifact.txt"],
            }
            created = loop.create_case(intake)
            crit_finding = finding("F-001", classification="requirement-violation")
            crit_finding["severity"] = "critical"
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [crit_finding],
                    "evidence": [],
                },
            )
            # Plan Gate for critical finding
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
                            "understanding": "Critical欠陥を修正する",
                            "disposition_intent": "fix",
                            "proposed_actions": ["修正"],
                        }
                    ],
                },
            )
            plan_reviewed = loop.review_plan(
                "QMS-0001",
                {
                    "operation_id": "op-rp-001",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-002",
                    "previous_handoff_id": planned["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-001",
                            "outcome": "plan-accepted",
                            "rationale": "了解",
                        }
                    ],
                },
            )
            submitted = loop.submit_response(
                "QMS-0001",
                {
                    "operation_id": "op-submit-001",
                    "actor_id": "implementer-001",
                    "role": "implementer",
                    "invocation_id": "inv-implementer-002",
                    "previous_handoff_id": plan_reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "changed_targets": ["artifact.txt"],
                    "responses": [
                        {
                            "finding_id": "F-001",
                            "disposition": "fix-submitted",
                            "rationale": "修正試行",
                            "evidence_refs": ["EV-01"],
                        }
                    ],
                    "evidence": [
                        {
                            "evidence_id": "EV-01",
                            "level": "observed",
                            "target_revision": "r2",
                            "method": "test",
                            "result": "fail",
                            "summary": "テスト失敗",
                        }
                    ],
                },
            )

            with self.assertRaises(QualityLoopError) as ctx:
                loop.verify(
                    "QMS-0001",
                    {
                        "operation_id": "op-verify-001",
                        "actor_id": "reviewer-003",
                        "role": "reviewer",
                        "invocation_id": "inv-reviewer-003",
                        "previous_handoff_id": submitted["handoff"]["handoff_id"],
                        "expected_case_revision": 5,
                        "verifications": [
                            {
                                "finding_id": "F-001",
                                "result": "not-remediated",
                                "rationale": "Critical指摘が未修正のまま",
                                "evidence_refs": ["EV-01"],
                            }
                        ],
                        "new_findings": [],
                        "change_observation": {
                            "method": "finite-manifest",
                            "scope": ["artifact.txt"],
                            "before_evidence_id": "EV-01",
                            "after_evidence_id": "EV-01",
                            "observed_changed_targets": ["artifact.txt"],
                            "limitations": [],
                        },
                        "evidence": [],
                        "early_risk_assessment": True,
                        "early_risk_rationale": "早く終わらせたい",
                    },
                )
            self.assertEqual("critical-finding-unresolved", ctx.exception.error_code)


if __name__ == "__main__":
    unittest.main()
