from __future__ import annotations

import tempfile
import unittest

from quality_loop import QualityLoop
from test_v1_3_p0 import make_finding, prepare_loop, risk_item


def review_findings(loop: QualityLoop, case_id: str, findings: list[dict], operation: str) -> dict:
    created = loop.store.load(case_id)
    return loop.review(
        case_id,
        {
            "operation_id": f"op-{operation}-review",
            "actor_id": "reviewer-v14",
            "role": "reviewer",
            "invocation_id": f"inv-{operation}-review",
            "previous_handoff_id": created["handoff"]["handoff_id"],
            "expected_case_revision": created["case_metadata"]["revision"],
            "findings": findings,
            "evidence": [],
        },
    )


def submit_responses(
    loop: QualityLoop,
    case_id: str,
    handoff: dict,
    finding_ids: list[str],
    operation: str,
) -> dict:
    revision = loop.store.load(case_id)["case_metadata"]["revision"]
    return loop.submit_response(
        case_id,
        {
            "operation_id": f"op-{operation}-response",
            "actor_id": "implementer-v14",
            "role": "implementer",
            "invocation_id": f"inv-{operation}-response",
            "previous_handoff_id": handoff["handoff_id"],
            "expected_case_revision": revision,
            "changed_targets": [],
            "responses": [
                {
                    "finding_id": finding_id,
                    "disposition": "accepted",
                    "rationale": "Verificationへ提出する",
                    "evidence_refs": [],
                }
                for finding_id in finding_ids
            ],
            "evidence": [],
        },
    )


def verify_findings(
    loop: QualityLoop,
    case_id: str,
    submitted: dict,
    results: list[dict],
    operation: str,
    new_findings: list[dict] | None = None,
) -> dict:
    revision = loop.store.load(case_id)["case_metadata"]["revision"]
    return loop.verify(
        case_id,
        {
            "operation_id": f"op-{operation}-verify",
            "actor_id": "reviewer-v14",
            "role": "reviewer",
            "invocation_id": f"inv-{operation}-verify",
            "previous_handoff_id": submitted["handoff"]["handoff_id"],
            "expected_case_revision": revision,
            "verifications": results,
            "new_findings": new_findings or [],
            "change_observation": None,
            "evidence": [],
        },
    )


def accept_high_plan(loop: QualityLoop, case_id: str, reviewed: dict, operation: str) -> dict:
    planned = loop.submit_plan(
        case_id,
        {
            "operation_id": f"op-{operation}-plan",
            "actor_id": "implementer-v14",
            "role": "implementer",
            "invocation_id": f"inv-{operation}-plan",
            "previous_handoff_id": reviewed["handoff"]["handoff_id"],
            "expected_case_revision": reviewed["case_revision"],
            "plans": [
                {
                    "finding_id": "F-HIGH",
                    "understanding": "再作業の条件と原因を確認する",
                    "disposition_intent": "fix",
                    "proposed_actions": ["再修正方針を実行する"],
                }
            ],
        },
    )
    return loop.review_plan(
        case_id,
        {
            "operation_id": f"op-{operation}-plan-review",
            "actor_id": "reviewer-v14",
            "role": "reviewer",
            "invocation_id": f"inv-{operation}-plan-review",
            "previous_handoff_id": planned["handoff"]["handoff_id"],
            "expected_case_revision": planned["case_revision"],
            "plan_reviews": [
                {
                    "finding_id": "F-HIGH",
                    "outcome": "plan-accepted",
                    "rationale": "再作業Planを承認する",
                }
            ],
        },
    )


def owner_rework(
    loop: QualityLoop,
    case_id: str,
    verified: dict,
    finding_id: str,
    severity: str,
) -> dict:
    assessed = loop.assess_risk(
        case_id,
        {
            "operation_id": "op-owner-rework-assess",
            "actor_id": "reviewer-v14",
            "role": "reviewer",
            "invocation_id": "inv-owner-rework-assess",
            "previous_handoff_id": verified["handoff"]["handoff_id"],
            "expected_case_revision": verified["case_revision"],
            "overall_recommendation": "require-remediation",
            "rationale": "未解決Findingの再作業が必要",
            "residual_risks": [risk_item(finding_id, "not-remediated", severity)],
        },
    )
    return loop.adjudicate(
        case_id,
        {
            "operation_id": "op-owner-rework",
            "actor_id": "owner-001",
            "role": "owner",
            "invocation_id": "inv-owner-rework",
            "previous_handoff_id": assessed["handoff"]["handoff_id"],
            "expected_case_revision": assessed["case_revision"],
            "decision": "rework-requested",
            "rationale": "追加修正を依頼する",
            "additional_cycles": 1,
        },
    )


class V14RepairAcceptanceTest(unittest.TestCase):
    def test_owner_rework_high_routes_to_submit_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir, case_id="QMS-V14-HIGH", cycle_limit=1)
            case_id = "QMS-V14-HIGH"
            reviewed = review_findings(
                loop, case_id, [make_finding("F-HIGH", "high")], "owner-high"
            )
            plan_reviewed = accept_high_plan(loop, case_id, reviewed, "owner-high")
            submitted = submit_responses(
                loop, case_id, plan_reviewed["handoff"], ["F-HIGH"], "owner-high"
            )
            verified = verify_findings(
                loop,
                case_id,
                submitted,
                [
                    {
                        "finding_id": "F-HIGH",
                        "result": "not-remediated",
                        "rationale": "修正後も未解決",
                        "evidence_refs": [],
                    }
                ],
                "owner-high",
            )
            self.assertEqual("assess-risk", verified["next_action"])

            reworked = owner_rework(loop, case_id, verified, "F-HIGH", "high")

            self.assertEqual("implementer", reworked["next_role"])
            self.assertEqual("submit-plan", reworked["next_action"])
            self.assertEqual("implementer-plan", loop.status(case_id)["current_state"])
            self.assertEqual(["F-HIGH"], reworked["handoff"]["open_items"])

    def test_owner_rework_handoff_allows_next_submit_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir, case_id="QMS-V14-HIGH-PLAN", cycle_limit=1)
            case_id = "QMS-V14-HIGH-PLAN"
            reviewed = review_findings(
                loop, case_id, [make_finding("F-HIGH", "high")], "owner-plan"
            )
            plan_reviewed = accept_high_plan(loop, case_id, reviewed, "owner-plan")
            submitted = submit_responses(
                loop, case_id, plan_reviewed["handoff"], ["F-HIGH"], "owner-plan"
            )
            verified = verify_findings(
                loop,
                case_id,
                submitted,
                [
                    {
                        "finding_id": "F-HIGH",
                        "result": "not-remediated",
                        "rationale": "再修正が必要",
                        "evidence_refs": [],
                    }
                ],
                "owner-plan",
            )
            reworked = owner_rework(loop, case_id, verified, "F-HIGH", "high")

            replanned = loop.submit_plan(
                case_id,
                {
                    "operation_id": "op-owner-plan-retry",
                    "actor_id": "implementer-v14",
                    "role": "implementer",
                    "invocation_id": "inv-owner-plan-retry",
                    "previous_handoff_id": reworked["handoff"]["handoff_id"],
                    "expected_case_revision": reworked["case_revision"],
                    "plans": [
                        {
                            "finding_id": "F-HIGH",
                            "understanding": "Owner rework後のPlanを確認した",
                            "disposition_intent": "fix",
                            "proposed_actions": ["追加修正する"],
                        }
                    ],
                },
            )

            self.assertEqual("reviewer", replanned["next_role"])
            self.assertEqual("review-plan", replanned["next_action"])
            self.assertEqual("reviewer-plan-review", loop.status(case_id)["current_state"])

    def test_owner_rework_low_routes_to_submit_response(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir, case_id="QMS-V14-LOW", cycle_limit=1)
            case_id = "QMS-V14-LOW"
            reviewed = review_findings(
                loop, case_id, [make_finding("F-LOW", "low", plan_required=False)], "owner-low"
            )
            submitted = submit_responses(
                loop, case_id, reviewed["handoff"], ["F-LOW"], "owner-low"
            )
            verified = verify_findings(
                loop,
                case_id,
                submitted,
                [
                    {
                        "finding_id": "F-LOW",
                        "result": "not-remediated",
                        "rationale": "軽微な指摘が残っている",
                        "evidence_refs": [],
                    }
                ],
                "owner-low",
            )
            reworked = owner_rework(loop, case_id, verified, "F-LOW", "low")

            self.assertEqual("implementer", reworked["next_role"])
            self.assertEqual("submit-response", reworked["next_action"])
            self.assertEqual("implementer-action", loop.status(case_id)["current_state"])

    def test_partial_verification_high_pending_routes_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir, case_id="QMS-V14-PARTIAL-HIGH", cycle_limit=3)
            case_id = "QMS-V14-PARTIAL-HIGH"
            reviewed = review_findings(
                loop,
                case_id,
                [make_finding("F-LOW", "low", plan_required=False)],
                "partial-high",
            )
            submitted = submit_responses(
                loop, case_id, reviewed["handoff"], ["F-LOW"], "partial-high"
            )
            verified = verify_findings(
                loop,
                case_id,
                submitted,
                [
                    {
                        "finding_id": "F-LOW",
                        "result": "remediated",
                        "rationale": "F-LOWを解消",
                        "evidence_refs": [],
                    }
                ],
                "partial-high",
                new_findings=[make_finding("F-HIGH", "high")],
            )

            self.assertEqual("implementer", verified["next_role"])
            self.assertEqual("submit-plan", verified["next_action"])
            self.assertEqual("implementer-plan", loop.status(case_id)["current_state"])
            self.assertEqual(["F-HIGH"], verified["handoff"]["open_items"])

    def test_partial_verification_low_pending_routes_response(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir, case_id="QMS-V14-PARTIAL-LOW", cycle_limit=3)
            case_id = "QMS-V14-PARTIAL-LOW"
            reviewed = review_findings(
                loop,
                case_id,
                [
                    make_finding("F-1", "low", plan_required=False),
                    make_finding("F-2", "low", plan_required=False),
                ],
                "partial-low",
            )
            submitted = submit_responses(
                loop, case_id, reviewed["handoff"], ["F-1"], "partial-low"
            )
            verified = verify_findings(
                loop,
                case_id,
                submitted,
                [
                    {
                        "finding_id": "F-1",
                        "result": "remediated",
                        "rationale": "F-1を解消",
                        "evidence_refs": [],
                    }
                ],
                "partial-low",
            )

            self.assertEqual("implementer", verified["next_role"])
            self.assertEqual("submit-response", verified["next_action"])
            self.assertEqual("implementer-action", loop.status(case_id)["current_state"])
            self.assertEqual(["F-2"], verified["handoff"]["open_items"])

    def test_all_material_resolved_routes_owner(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir, case_id="QMS-V14-RESOLVED", cycle_limit=3)
            case_id = "QMS-V14-RESOLVED"
            reviewed = review_findings(
                loop,
                case_id,
                [
                    make_finding("F-1", "low", plan_required=False),
                    make_finding("F-2", "low", plan_required=False),
                ],
                "resolved",
            )
            submitted = submit_responses(
                loop, case_id, reviewed["handoff"], ["F-1", "F-2"], "resolved"
            )
            verified = verify_findings(
                loop,
                case_id,
                submitted,
                [
                    {
                        "finding_id": "F-1",
                        "result": "remediated",
                        "rationale": "F-1を解消",
                        "evidence_refs": [],
                    },
                    {
                        "finding_id": "F-2",
                        "result": "remediated",
                        "rationale": "F-2を解消",
                        "evidence_refs": [],
                    },
                ],
                "resolved",
            )

            self.assertEqual("owner", verified["next_role"])
            self.assertEqual("adjudicate", verified["next_action"])
            self.assertEqual("owner-adjudication", loop.status(case_id)["current_state"])


if __name__ == "__main__":
    unittest.main()
