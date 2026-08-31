from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from quality_loop import QualityLoop, QualityLoopError
from test_quality_loop import complete_intake


def make_finding(finding_id: str, severity: str = "low", **extra: object) -> dict:
    finding = {
        "finding_id": finding_id,
        "classification": "requirement-violation",
        "severity": severity,
        "requirement_ref": "REQ-001",
        "observed_fact": f"{finding_id}の事実",
        "impact": f"{finding_id}の影響",
        "expected_state": "要求を満たす",
        "verification_method": "独立検証",
        "evidence_refs": [],
        "status": "open",
    }
    finding.update(extra)
    return finding


def prepare_loop(temp_dir: str, case_id: str = "QMS-0001", *, cycle_limit: int = 1) -> QualityLoop:
    loop = QualityLoop(Path(temp_dir))
    intake = complete_intake()
    intake["case_id"] = case_id
    intake["cycle_limit"] = cycle_limit
    intake["implementation_authorization"] = {
        "allowed": True,
        "finding_ids": ["F-HIGH", "F-LOW", "F-1", "F-2"],
        "allowed_targets": ["artifact.txt"],
    }
    loop.create_case(intake)
    return loop


def enter_final_risk(loop: QualityLoop, findings: list[dict], case_id: str = "QMS-0001") -> dict:
    created = loop.store.load(case_id)
    reviewed = loop.review(
        case_id,
        {
            "operation_id": "op-review-v13",
            "actor_id": "reviewer-v13",
            "role": "reviewer",
            "invocation_id": "inv-review-v13",
            "previous_handoff_id": created["handoff"]["handoff_id"],
            "expected_case_revision": 1,
            "findings": findings,
            "evidence": [],
        },
    )
    submitted = loop.submit_response(
        case_id,
        {
            "operation_id": "op-response-v13",
            "actor_id": "implementer-v13",
            "role": "implementer",
            "invocation_id": "inv-implementer-v13",
            "previous_handoff_id": reviewed["handoff"]["handoff_id"],
            "expected_case_revision": 2,
            "changed_targets": [],
            "responses": [
                {
                    "finding_id": finding["finding_id"],
                    "disposition": "accepted",
                    "rationale": "現状を受領した",
                    "evidence_refs": [],
                }
                for finding in findings
            ],
            "evidence": [],
        },
    )
    verified = loop.verify(
        case_id,
        {
            "operation_id": "op-verify-v13",
            "actor_id": "reviewer-v13",
            "role": "reviewer",
            "invocation_id": "inv-reviewer-verify-v13",
            "previous_handoff_id": submitted["handoff"]["handoff_id"],
            "expected_case_revision": 3,
            "verifications": [
                {
                    "finding_id": finding["finding_id"],
                    "result": "unverified",
                    "rationale": "追加Evidenceがなく未検証",
                    "evidence_refs": [],
                }
                for finding in findings
            ],
            "new_findings": [],
            "change_observation": None,
            "evidence": [],
        },
    )
    return verified


def risk_item(finding_id: str, status: str = "unverified", severity: str = "low") -> dict:
    return {
        "finding_id": finding_id,
        "current_status": status,
        "severity": severity,
        "residual_risk_description": f"{finding_id}の残余リスク",
        "likelihood": "low",
        "impact": "low",
        "qa_recommendation": "accept-with-conditions",
        "confidence": "high",
    }


class PlanGateV13Test(unittest.TestCase):
    def test_partial_plan_cannot_open_global_response_phase(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir)
            created = loop.store.load("QMS-0001")
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-v13-plan",
                    "actor_id": "reviewer-v13",
                    "role": "reviewer",
                    "invocation_id": "inv-review-v13-plan",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        make_finding("F-HIGH", "high", plan_required=False),
                        make_finding("F-LOW", "low", plan_required=False),
                    ],
                    "evidence": [],
                },
            )
            planned = loop.submit_plan(
                "QMS-0001",
                {
                    "operation_id": "op-plan-v13-low",
                    "actor_id": "implementer-v13",
                    "role": "implementer",
                    "invocation_id": "inv-implementer-v13-plan",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [
                        {
                            "finding_id": "F-LOW",
                            "understanding": "軽微な修正を確認する",
                            "disposition_intent": "fix",
                            "proposed_actions": ["表記を確認する"],
                        }
                    ],
                },
            )
            plan_reviewed = loop.review_plan(
                "QMS-0001",
                {
                    "operation_id": "op-review-plan-v13-low",
                    "actor_id": "reviewer-v13",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-v13-plan-review",
                    "previous_handoff_id": planned["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "plan_reviews": [
                        {
                            "finding_id": "F-LOW",
                            "outcome": "plan-accepted",
                            "rationale": "軽微なPlanを承認",
                        }
                    ],
                },
            )

            self.assertEqual("submit-plan", plan_reviewed["next_action"])
            self.assertEqual(["F-HIGH"], plan_reviewed["handoff"]["open_items"])
            before = loop.store.load("QMS-0001")["case_metadata"]["revision"]
            with self.assertRaises(QualityLoopError) as captured:
                loop.submit_response(
                    "QMS-0001",
                    {
                        "operation_id": "op-bypass-v13",
                        "actor_id": "implementer-v13",
                        "role": "implementer",
                        "invocation_id": "inv-implementer-v13-bypass",
                        "previous_handoff_id": plan_reviewed["handoff"]["handoff_id"],
                        "expected_case_revision": before,
                        "changed_targets": ["artifact.txt"],
                        "responses": [
                            {
                                "finding_id": "F-HIGH",
                                "disposition": "fix-submitted",
                                "rationale": "Planなしで修正を試みる",
                                "evidence_refs": [],
                            }
                        ],
                        "evidence": [],
                    },
                )
            self.assertEqual("state-transition-not-allowed", captured.exception.error_code)
            self.assertEqual(before, loop.store.load("QMS-0001")["case_metadata"]["revision"])

    def test_high_plan_required_flag_cannot_be_lowered_by_review_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir)
            created = loop.store.load("QMS-0001")
            result = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-v13-downlevel",
                    "actor_id": "reviewer-v13",
                    "role": "reviewer",
                    "invocation_id": "inv-review-v13-downlevel",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [make_finding("F-HIGH", "high", plan_required=False)],
                    "evidence": [],
                },
            )
            case = loop.store.load("QMS-0001")
            self.assertTrue(case["findings"][0]["plan_required"])
            self.assertEqual("submit-plan", result["next_action"])

    def test_review_cannot_forge_plan_approved_finding_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir)
            created = loop.store.load("QMS-0001")
            loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-v13-forged-status",
                    "actor_id": "reviewer-v13",
                    "role": "reviewer",
                    "invocation_id": "inv-review-v13-forged-status",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [make_finding("F-HIGH", "high", status="plan-approved")],
                    "evidence": [],
                },
            )
            case = loop.store.load("QMS-0001")
            self.assertEqual("open", case["findings"][0]["status"])
            self.assertEqual(set(), loop._approved_plan_finding_ids(case))

    def test_submit_plan_rejects_in_progress_and_completed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir)
            created = loop.store.load("QMS-0001")
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-v13-status",
                    "actor_id": "reviewer-v13",
                    "role": "reviewer",
                    "invocation_id": "inv-review-v13-status",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [make_finding("F-HIGH", "high")],
                    "evidence": [],
                },
            )
            base = {
                "actor_id": "implementer-v13",
                "role": "implementer",
                "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                "expected_case_revision": 2,
            }
            for index, status in enumerate(("in-progress", "completed"), start=1):
                with self.assertRaises(QualityLoopError) as captured:
                    loop.submit_plan(
                        "QMS-0001",
                        {
                            **base,
                            "operation_id": f"op-plan-v13-{index}",
                            "invocation_id": f"inv-plan-v13-{index}",
                            "plans": [
                                {
                                    "finding_id": "F-HIGH",
                                    "understanding": "問題を理解した",
                                    "disposition_intent": "fix",
                                    "proposed_actions": ["修正する"],
                                    "implementation_status": status,
                                }
                            ],
                        },
                    )
                self.assertEqual("invalid-plan-status", captured.exception.error_code)
                self.assertEqual(2, loop.store.load("QMS-0001")["case_metadata"]["revision"])

            accepted = loop.submit_plan(
                "QMS-0001",
                {
                    **base,
                    "operation_id": "op-plan-v13-valid",
                    "invocation_id": "inv-plan-v13-valid",
                    "plans": [
                        {
                            "finding_id": "F-HIGH",
                            "understanding": "問題を理解した",
                            "disposition_intent": "fix",
                            "proposed_actions": ["修正する"],
                            "implementation_status": "not-started",
                        }
                    ],
                },
            )
            self.assertEqual(3, accepted["case_revision"])


class FinalRiskCoverageV13Test(unittest.TestCase):
    def assess(self, loop: QualityLoop, handoff: dict, revision: int, risks: list[dict]) -> dict:
        return loop.assess_risk(
            "QMS-0001",
            {
                "operation_id": f"op-assess-v13-{revision}-{len(risks)}",
                "actor_id": "reviewer-v13",
                "role": "reviewer",
                "invocation_id": f"inv-assess-v13-{revision}-{len(risks)}",
                "previous_handoff_id": handoff["handoff_id"],
                "expected_case_revision": revision,
                "overall_recommendation": "accept-with-conditions",
                "rationale": "全material unresolved Findingを評価する",
                "residual_risks": risks,
            },
        )

    def test_missing_material_finding_is_rejected_without_revision_change(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir)
            handoff = enter_final_risk(loop, [make_finding("F-1"), make_finding("F-2")])
            with self.assertRaises(QualityLoopError) as captured:
                self.assess(loop, handoff["handoff"], 4, [risk_item("F-1")])
            self.assertEqual("residual-risk-coverage-incomplete", captured.exception.error_code)
            case = loop.store.load("QMS-0001")
            self.assertEqual(4, case["case_metadata"]["revision"])
            self.assertEqual([], case["final_risk_assessments"])

    def test_complete_material_coverage_is_accepted_and_rendered(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir)
            handoff = enter_final_risk(loop, [make_finding("F-1"), make_finding("F-2")])
            result = self.assess(
                loop,
                handoff["handoff"],
                4,
                [risk_item("F-1"), risk_item("F-2")],
            )
            self.assertEqual("adjudicate", result["next_action"])
            report = (Path(temp_dir) / "QMS-0001" / "final-risk-assessment.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("F-1", report)
            self.assertIn("F-2", report)
            self.assertIn("Final Risk coverage**: 2/2", report)

    def test_withdrawn_finding_is_not_required_for_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir)
            created = loop.store.load("QMS-0001")
            reviewed = loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-v13-withdraw",
                    "actor_id": "reviewer-v13",
                    "role": "reviewer",
                    "invocation_id": "inv-review-v13-withdraw",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [make_finding("F-1"), make_finding("F-2")],
                    "evidence": [],
                },
            )
            submitted = loop.submit_response(
                "QMS-0001",
                {
                    "operation_id": "op-response-v13-withdraw",
                    "actor_id": "implementer-v13",
                    "role": "implementer",
                    "invocation_id": "inv-response-v13-withdraw",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "changed_targets": [],
                    "responses": [
                        {
                            "finding_id": "F-1",
                            "disposition": "accepted",
                            "rationale": "撤回に異議なし",
                            "evidence_refs": [],
                        },
                        {
                            "finding_id": "F-2",
                            "disposition": "accepted",
                            "rationale": "未検証として扱う",
                            "evidence_refs": [],
                        },
                    ],
                    "evidence": [],
                },
            )
            verified = loop.verify(
                "QMS-0001",
                {
                    "operation_id": "op-verify-v13-withdraw",
                    "actor_id": "reviewer-v13",
                    "role": "reviewer",
                    "invocation_id": "inv-verify-v13-withdraw",
                    "previous_handoff_id": submitted["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "verifications": [
                        {
                            "finding_id": "F-1",
                            "result": "finding-withdrawn",
                            "rationale": "初期事実が成立しない",
                            "evidence_refs": [],
                        },
                        {
                            "finding_id": "F-2",
                            "result": "unverified",
                            "rationale": "Evidence不足",
                            "evidence_refs": [],
                        },
                    ],
                    "new_findings": [],
                    "change_observation": None,
                    "evidence": [],
                },
            )
            result = self.assess(loop, verified["handoff"], 4, [risk_item("F-2")])
            self.assertEqual("adjudicate", result["next_action"])

    def test_status_and_severity_mismatch_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir)
            handoff = enter_final_risk(loop, [make_finding("F-1")])
            with self.assertRaises(QualityLoopError) as status_error:
                self.assess(loop, handoff["handoff"], 4, [risk_item("F-1", "remediated")])
            self.assertEqual("risk-status-mismatch", status_error.exception.error_code)
            with self.assertRaises(QualityLoopError) as severity_error:
                self.assess(loop, handoff["handoff"], 4, [risk_item("F-1", severity="high")])
            self.assertEqual("risk-severity-mismatch", severity_error.exception.error_code)


if __name__ == "__main__":
    unittest.main()
