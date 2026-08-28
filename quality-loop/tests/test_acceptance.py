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
        "unverified_reason": "テスト用の観測Evidenceを登録していない",
        "required_evidence": "対象成果物の独立観測記録",
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

            rereviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-rereview-001",
                    "actor_id": "reviewer-002",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-rereview-001",
                    "previous_handoff_id": result["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "findings": [],
                    "rereviews": [
                        {
                            "finding_id": "F-001",
                            "result": "verified",
                            "rationale": "変更後baselineに対する不適合は確認されない",
                            "evidence_refs": ["EV-REREVIEW-001"],
                        }
                    ],
                    "evidence": [
                        {
                            "evidence_id": "EV-REREVIEW-001",
                            "level": "observed",
                            "target_revision": "r2",
                            "method": "変更後baselineの独立確認",
                            "result": "passed",
                            "summary": "要求と対象成果物を再照合した",
                        }
                    ],
                },
            )
            self.assertEqual("owner", rereviewed["next_role"])
            finding_after_rereview = loop.store.load("QMS-0001")["findings"][0]
            self.assertEqual("verified", finding_after_rereview["status"])
            self.assertEqual(1, len(finding_after_rereview["rereviews"]))


class EvidenceGapAndCycleLimitAcceptanceTest(unittest.TestCase):
    def test_risk_acceptance_requires_conditions_and_review_trigger(self) -> None:
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
                "operation_id": "op-risk-001",
                "actor_id": "owner-001",
                "role": "owner",
                "invocation_id": "inv-owner-risk-001",
                "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                "expected_case_revision": 2,
                "decision": "accepted-with-risk",
                "rationale": "残余リスクを受容する",
                "residual_risks": ["外部依存先の確認待ち"],
                "confirm": True,
            }
            with self.assertRaises(QualityLoopError) as conditions_error:
                loop.adjudicate("QMS-0001", base)
            self.assertEqual("risk-conditions-required", conditions_error.exception.error_code)
            with self.assertRaises(QualityLoopError) as trigger_error:
                loop.adjudicate(
                    "QMS-0001", {**base, "conditions": ["外部確認を実施する"]}
                )
            self.assertEqual("risk-review-trigger-required", trigger_error.exception.error_code)
    def test_unverified_without_implementation_authorization_routes_to_owner(self) -> None:
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
                    "findings": [finding(classification="evidence-gap")],
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
                            "rationale": "Ownerの実装許可がない",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )
            result = loop.verify(
                "QMS-0001",
                {
                    "operation_id": "op-verify-001",
                    "actor_id": "reviewer-002",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-verify-001",
                    "previous_handoff_id": submitted["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "verifications": [
                        {
                            "finding_id": "F-001",
                            "result": "unverified",
                            "rationale": "許可されていないため変更の有効性を確認できない",
                            "evidence_refs": [],
                            "unverified_reason": "Ownerの実装許可がない",
                            "required_evidence": "許可後の修正・検証記録",
                        }
                    ],
                    "new_findings": [],
                    "change_observation": None,
                    "evidence": [],
                },
            )
            self.assertEqual("owner", result["next_role"])
            self.assertEqual("adjudicate", result["next_action"])

    def test_unverified_stays_distinct_and_third_cycle_routes_to_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            intake = complete_intake()
            intake["implementation_authorization"] = {
                "allowed": True,
                "finding_ids": ["F-001"],
                "allowed_targets": [],
            }
            created = loop.create_case(intake)
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
                                "unverified_reason": "必要な外部環境がない",
                                "required_evidence": "外部環境での独立実行記録",
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
                    self.assertEqual("owner", handoff["next_role"])

            case = loop.store.load("QMS-0001")
            self.assertEqual("unverified", case["findings"][0]["status"])
            self.assertEqual(3, case["case_metadata"]["cycle_count"])
            self.assertEqual("owner-adjudication", case["case_metadata"]["status"])

            accepted = loop.adjudicate(
                "QMS-0001",
                {
                    "operation_id": "op-adjudicate-001",
                    "actor_id": "owner-001",
                    "role": "owner",
                    "invocation_id": "inv-owner-002",
                    "previous_handoff_id": handoff["handoff"]["handoff_id"],
                    "expected_case_revision": revision,
                    "decision": "accepted-with-risk",
                    "rationale": "外部環境での確認を期限付き残余リスクとして受容する",
                    "conditions": ["2026-09-30までに外部環境で再確認する"],
                    "residual_risks": ["外部環境の動作は未検証"],
                    "review_trigger": "2026-09-30または外部環境が利用可能になった時点",
                    "dry_run": False,
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
            intake = complete_intake()
            intake["implementation_authorization"] = {
                "allowed": True,
                "finding_ids": ["F-001"],
                "allowed_targets": [],
            }
            created = loop.create_case(intake)
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
                                "unverified_reason": "必要な外部環境がない",
                                "required_evidence": "外部環境での独立実行記録",
                            }
                        ],
                        "new_findings": [],
                        "change_observation": None,
                        "evidence": [],
                    },
                )
                revision += 1

            base = {
                "actor_id": "owner-001",
                "role": "owner",
                "invocation_id": "inv-owner-002",
                "previous_handoff_id": handoff["handoff"]["handoff_id"],
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
            intake = complete_intake()
            intake["implementation_authorization"] = {
                "allowed": True,
                "finding_ids": ["F-001", "F-002"],
                "allowed_targets": [],
            }
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


if __name__ == "__main__":
    unittest.main()
