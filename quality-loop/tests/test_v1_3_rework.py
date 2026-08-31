from __future__ import annotations

import tempfile
import unittest

from quality_loop import QualityLoop
from test_v1_3_p0 import make_finding, prepare_loop


def plan_for(finding_id: str) -> dict:
    return {
        "finding_id": finding_id,
        "understanding": "指摘の再発条件と修正方針を確認した",
        "disposition_intent": "fix",
        "proposed_actions": ["修正方針に沿って再対応する"],
    }


def review_plan_payload(previous_handoff_id: str, revision: int, operation_id: str) -> dict:
    return {
        "operation_id": operation_id,
        "actor_id": "reviewer-v13-rework",
        "role": "reviewer",
        "invocation_id": f"inv-{operation_id}",
        "previous_handoff_id": previous_handoff_id,
        "expected_case_revision": revision,
        "plan_reviews": [
            {
                "finding_id": "F-HIGH",
                "outcome": "plan-accepted",
                "rationale": "再対応方針を承認する",
            }
        ],
    }


class ReworkRoutingV13Test(unittest.TestCase):
    def test_not_remediated_high_routes_to_new_plan_without_deadlock(self) -> None:
        """High Findingの再作業では、Responseではなく新しいPlanへ戻る。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir, case_id="QMS-REWORK-01", cycle_limit=3)
            case_id = "QMS-REWORK-01"
            created = loop.store.load(case_id)
            reviewed = loop.review(
                case_id,
                {
                    "operation_id": "op-rework-review",
                    "actor_id": "reviewer-v13-rework",
                    "role": "reviewer",
                    "invocation_id": "inv-rework-review",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [make_finding("F-HIGH", "high")],
                    "evidence": [],
                },
            )
            planned = loop.submit_plan(
                case_id,
                {
                    "operation_id": "op-rework-plan-1",
                    "actor_id": "implementer-v13-rework",
                    "role": "implementer",
                    "invocation_id": "inv-rework-plan-1",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "plans": [plan_for("F-HIGH")],
                },
            )
            plan_reviewed = loop.review_plan(
                case_id,
                review_plan_payload(
                    planned["handoff"]["handoff_id"], 3, "op-rework-plan-review-1"
                ),
            )
            submitted = loop.submit_response(
                case_id,
                {
                    "operation_id": "op-rework-response-1",
                    "actor_id": "implementer-v13-rework",
                    "role": "implementer",
                    "invocation_id": "inv-rework-response-1",
                    "previous_handoff_id": plan_reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 4,
                    "changed_targets": [],
                    "responses": [
                        {
                            "finding_id": "F-HIGH",
                            "disposition": "accepted",
                            "rationale": "修正結果を検証へ提出する",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )

            verified = loop.verify(
                case_id,
                {
                    "operation_id": "op-rework-verify-1",
                    "actor_id": "reviewer-v13-rework",
                    "role": "reviewer",
                    "invocation_id": "inv-rework-verify-1",
                    "previous_handoff_id": submitted["handoff"]["handoff_id"],
                    "expected_case_revision": 5,
                    "verifications": [
                        {
                            "finding_id": "F-HIGH",
                            "result": "not-remediated",
                            "rationale": "修正後も指摘が残っている",
                            "evidence_refs": [],
                        }
                    ],
                    "new_findings": [],
                    "change_observation": None,
                    "evidence": [],
                },
            )

            self.assertEqual("implementer", verified["next_role"])
            self.assertEqual("submit-plan", verified["next_action"])
            self.assertEqual("implementer-plan", loop.status(case_id)["current_state"])
            self.assertEqual(["F-HIGH"], verified["handoff"]["open_items"])

            replanned = loop.submit_plan(
                case_id,
                {
                    "operation_id": "op-rework-plan-2",
                    "actor_id": "implementer-v13-rework",
                    "role": "implementer",
                    "invocation_id": "inv-rework-plan-2",
                    "previous_handoff_id": verified["handoff"]["handoff_id"],
                    "expected_case_revision": 6,
                    "plans": [plan_for("F-HIGH")],
                },
            )
            replanned_review = loop.review_plan(
                case_id,
                review_plan_payload(
                    replanned["handoff"]["handoff_id"], 7, "op-rework-plan-review-2"
                ),
            )
            self.assertEqual("submit-response", replanned_review["next_action"])

            response_again = loop.submit_response(
                case_id,
                {
                    "operation_id": "op-rework-response-2",
                    "actor_id": "implementer-v13-rework",
                    "role": "implementer",
                    "invocation_id": "inv-rework-response-2",
                    "previous_handoff_id": replanned_review["handoff"]["handoff_id"],
                    "expected_case_revision": 8,
                    "changed_targets": [],
                    "responses": [
                        {
                            "finding_id": "F-HIGH",
                            "disposition": "accepted",
                            "rationale": "再承認されたPlanに基づき再提出する",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )
            self.assertEqual("verify", response_again["next_action"])

    def test_new_high_finding_during_verification_routes_to_plan(self) -> None:
        """Verificationで追加されたHigh Findingも、PlanなしのResponseへ進めない。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir, case_id="QMS-REWORK-02", cycle_limit=3)
            case_id = "QMS-REWORK-02"
            created = loop.store.load(case_id)
            reviewed = loop.review(
                case_id,
                {
                    "operation_id": "op-new-high-review",
                    "actor_id": "reviewer-v13-rework",
                    "role": "reviewer",
                    "invocation_id": "inv-new-high-review",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [make_finding("F-LOW", "low", plan_required=False)],
                    "evidence": [],
                },
            )
            submitted = loop.submit_response(
                case_id,
                {
                    "operation_id": "op-new-high-response",
                    "actor_id": "implementer-v13-rework",
                    "role": "implementer",
                    "invocation_id": "inv-new-high-response",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "changed_targets": [],
                    "responses": [
                        {
                            "finding_id": "F-LOW",
                            "disposition": "accepted",
                            "rationale": "既存の軽微な指摘を検証へ提出する",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )
            verified = loop.verify(
                case_id,
                {
                    "operation_id": "op-new-high-verify",
                    "actor_id": "reviewer-v13-rework",
                    "role": "reviewer",
                    "invocation_id": "inv-new-high-verify",
                    "previous_handoff_id": submitted["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "verifications": [
                        {
                            "finding_id": "F-LOW",
                            "result": "not-remediated",
                            "rationale": "軽微な指摘が残っている",
                            "evidence_refs": [],
                        }
                    ],
                    "new_findings": [make_finding("F-1", "high")],
                    "change_observation": None,
                    "evidence": [],
                },
            )

            self.assertEqual("implementer", verified["next_role"])
            self.assertEqual("submit-plan", verified["next_action"])
            self.assertEqual(["F-1"], verified["handoff"]["open_items"])

    def test_low_rework_keeps_direct_response_routing(self) -> None:
        """Plan不要のLow Findingは、従来どおり直接Responseへ進む。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = prepare_loop(temp_dir, case_id="QMS-REWORK-03", cycle_limit=3)
            case_id = "QMS-REWORK-03"
            created = loop.store.load(case_id)
            reviewed = loop.review(
                case_id,
                {
                    "operation_id": "op-low-review",
                    "actor_id": "reviewer-v13-rework",
                    "role": "reviewer",
                    "invocation_id": "inv-low-review",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [make_finding("F-LOW", "low", plan_required=False)],
                    "evidence": [],
                },
            )
            submitted = loop.submit_response(
                case_id,
                {
                    "operation_id": "op-low-response",
                    "actor_id": "implementer-v13-rework",
                    "role": "implementer",
                    "invocation_id": "inv-low-response",
                    "previous_handoff_id": reviewed["handoff"]["handoff_id"],
                    "expected_case_revision": 2,
                    "changed_targets": [],
                    "responses": [
                        {
                            "finding_id": "F-LOW",
                            "disposition": "accepted",
                            "rationale": "軽微な指摘を検証へ提出する",
                            "evidence_refs": [],
                        }
                    ],
                    "evidence": [],
                },
            )
            verified = loop.verify(
                case_id,
                {
                    "operation_id": "op-low-verify",
                    "actor_id": "reviewer-v13-rework",
                    "role": "reviewer",
                    "invocation_id": "inv-low-verify",
                    "previous_handoff_id": submitted["handoff"]["handoff_id"],
                    "expected_case_revision": 3,
                    "verifications": [
                        {
                            "finding_id": "F-LOW",
                            "result": "not-remediated",
                            "rationale": "軽微な指摘が残っている",
                            "evidence_refs": [],
                        }
                    ],
                    "new_findings": [],
                    "change_observation": None,
                    "evidence": [],
                },
            )

            self.assertEqual("implementer", verified["next_role"])
            self.assertEqual("submit-response", verified["next_action"])
            self.assertEqual("implementer-action", loop.status(case_id)["current_state"])


if __name__ == "__main__":
    unittest.main()
