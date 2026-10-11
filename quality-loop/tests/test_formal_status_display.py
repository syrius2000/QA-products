from __future__ import annotations

import copy
import unittest

from quality_loop.status_display import (
    CASE_STATUS_STAGES,
    FINDING_RESULT_LABELS,
    RECOMMENDATION_LABELS,
    render_case_status,
    stage_for_case_status,
)


class FormalStatusDisplayTests(unittest.TestCase):
    def status(self, state: str, **overrides) -> dict:
        result = {
            "case_id": "QMS-0001",
            "case_revision": 7,
            "current_state": state,
            "next_role": "reviewer",
            "next_action": "verify",
            "handoff": {
                "next_role": "reviewer",
                "next_action": "verify",
                "purpose": "提出された修正を独立検証する",
            },
            "open_findings": [],
            "evidence_gaps": [],
            "owner_decisions_required": False,
            "implementation_authorization": {
                "allowed": False,
                "allowed_targets": [],
            },
        }
        result.update(overrides)
        return result

    def test_all_eleven_formal_states_map_to_the_five_stages(self) -> None:
        expected = {
            "reviewer-action": "QA・確認",
            "reviewer-plan-review": "QA・確認",
            "reviewer-verification": "QA・確認",
            "reviewer-final-assessment": "QA・確認",
            "implementer-plan": "修正",
            "implementer-action": "修正",
            "owner-adjudication": "判断待ち",
            "held": "判断待ち",
            "accepted": "終了",
            "accepted-with-risk": "終了",
            "rejected": "終了",
        }
        self.assertEqual(11, len(CASE_STATUS_STAGES))
        for state, stage in expected.items():
            with self.subTest(state=state):
                self.assertEqual(stage, stage_for_case_status(self.status(state))[0])

    def test_unknown_state_is_not_guessed_as_success(self) -> None:
        stage, detail = stage_for_case_status(self.status("unexpected"))
        self.assertEqual("未定義", stage)
        self.assertIn("unexpected", detail)
        self.assertNotEqual("終了", stage)

    def test_compound_hold_preserves_stop_reason_findings_evidence_and_results(self) -> None:
        status = self.status(
            "held",
            owner_decisions_required=True,
            open_findings=["QA-F01", "QA-F03"],
            evidence_gaps=["QA-F03"],
            handoff={
                "next_role": "owner",
                "next_action": "adjudicate",
                "purpose": "追加Evidenceを確認してOwner裁定を再開する",
            },
        )
        case = {
            "case_metadata": {"cycle_count": 2, "cycle_limit": 3},
            "baseline": {"target_revision": "target-v2.4"},
            "implementation_authorization": {"allowed": False, "allowed_targets": []},
            "findings": [{"finding_id": "QA-F01", "status": "requires-rereview"}],
            "verifications": [
                {"finding_id": "QA-F01", "result": "unverified", "verification_revision": 5},
                {"finding_id": "QA-F01", "result": "partially-remediated", "verification_revision": 6},
            ],
            "final_risk_assessments": [
                {"overall_recommendation": "defer"},
            ],
            "adjudications": [
                {"decision": "held", "rationale": "必要なEvidenceが未提出"},
            ],
        }
        before_status = copy.deepcopy(status)
        before_case = copy.deepcopy(case)
        output = render_case_status(status, case=case)
        self.assertIn("工程: 判断待ち", output)
        self.assertIn("停止中", output)
        self.assertIn("Ownerの裁定が必要", output)
        self.assertIn("QA-F01, QA-F03", output)
        self.assertIn("Evidence不足: 1件（QA-F03）", output)
        self.assertIn("Reviewer評価勧告: 未記録（現在版）", output)
        self.assertIn("対象版・サイクル未特定）: 判断延期推奨（defer）", output)
        self.assertIn("検証結果: QA-F01＝一部修正（partially-remediated", output)
        self.assertIn("保留理由: 必要なEvidenceが未提出", output)
        self.assertIn("評価対象版（baseline.target_revision）: target-v2.4", output)
        self.assertIn("サイクル: 2/3", output)
        self.assertEqual(before_status, status)
        self.assertEqual(before_case, case)

    def test_risk_recommendation_is_bound_to_record_revision_in_both_languages(self) -> None:
        case = {
            "case_metadata": {"revision": 5, "cycle_count": 2, "cycle_limit": 3},
            "baseline": {"target_revision": "rev-1"},
            "final_risk_assessments": [{"revision": 5, "overall_recommendation": "accept"}],
        }
        status = self.status("owner-adjudication")
        current = render_case_status(status, case=case)
        self.assertIn("Reviewer評価勧告: 受入推奨（accept） ／ 対象版 rev-1 ／ サイクル 2", current)
        case["case_metadata"].update(revision=6, cycle_count=3)
        case["baseline"]["target_revision"] = "rev-2"
        before = copy.deepcopy(case)
        ja = render_case_status(status, case=case)
        en = render_case_status(status, case=case, lang="en")
        self.assertIn("Reviewer評価勧告: 未記録（現在版）。過去評価（case Revision 5", ja)
        self.assertIn("対象版・サイクル未特定", ja)
        self.assertIn("Reviewer recommendation: not recorded for current revision; historical assessment", en)
        self.assertIn("case Revision 5, target and cycle unknown): accept", en)
        self.assertEqual(before, case)

    def test_terminal_decisions_keep_distinct_meanings_even_with_open_findings(self) -> None:
        cases = (
            ("accepted", "Ownerが受入を確定"),
            ("accepted-with-risk", "残余リスク付き受入を確定"),
            ("rejected", "Ownerが案件を却下"),
        )
        for state, detail in cases:
            with self.subTest(state=state):
                status = self.status(state, open_findings=["QA-F01"])
                output = render_case_status(status)
                self.assertIn("工程: 終了", output)
                self.assertIn(detail, output)
                self.assertIn("未解決Finding: 1件（QA-F01）", output)

    def test_verification_and_recommendation_values_remain_separate(self) -> None:
        self.assertIn("verified", FINDING_RESULT_LABELS)
        self.assertIn("not-verified", FINDING_RESULT_LABELS)
        self.assertIn("accept", RECOMMENDATION_LABELS)
        self.assertIn("accept-with-conditions", RECOMMENDATION_LABELS)
        self.assertIn("require-remediation", RECOMMENDATION_LABELS)
        self.assertIn("defer", RECOMMENDATION_LABELS)
        output = render_case_status(
            self.status("owner-adjudication"),
            case={
                "case_metadata": {"revision": 7, "cycle_count": 2},
                "final_risk_assessments": [{"revision": 7, "overall_recommendation": "accept-with-conditions"}],
                "verifications": [{"finding_id": "QA-F01", "result": "verified", "verification_revision": 6}],
            },
        )
        self.assertIn("Reviewer評価勧告: 条件付き受入推奨（accept-with-conditions）", output)
        self.assertIn("検証結果: QA-F01＝検証済み（verified", output)

    def test_missing_formal_target_revision_is_explicitly_unidentified(self) -> None:
        output = render_case_status(
            self.status("reviewer-action"),
            case={"baseline": {}, "case_metadata": {"cycle_count": 0, "cycle_limit": 3}},
        )
        self.assertIn("評価対象版（baseline.target_revision）: 未特定", output)
        self.assertIn("サイクル: 0/3", output)

    def test_english_keeps_machine_codes_and_rejects_invalid_language(self) -> None:
        output = render_case_status(self.status("rejected"), lang="en")
        self.assertIn("state rejected", output)
        self.assertIn("Stage: 終了", output)
        with self.assertRaisesRegex(ValueError, "jaまたはen"):
            render_case_status(self.status("accepted"), lang="fr")


if __name__ == "__main__":
    unittest.main()
