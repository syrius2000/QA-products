from __future__ import annotations

import unittest

from qa_workflow.status_display import (
    QA_GATE_LABELS,
    assessment_from_state,
    render_status,
    resolve_assessments,
    stage_for_status,
)


class QualityQaStatusDisplayTests(unittest.TestCase):
    def status(self, phase: str, *, reason: str = "", action: str = "続行") -> dict:
        return {
            "id": "QA-0001",
            "cycle": 2,
            "phase": phase,
            "next": {
                "担当": "確認担当",
                "操作": action,
                "理由": reason,
                "必要入力": "review.md",
            },
        }

    def test_known_phases_map_to_five_user_stages(self) -> None:
        expected = {
            "draft": "準備",
            "prepared": "準備",
            "published": "QA・確認",
            "waiting": "QA・確認",
            "content_pending": "QA・確認",
            "invalid": "QA・確認",
            "planned": "判断待ち",
            "approved": "修正",
            "submitted": "QA・確認",
            "decision": "終了",
        }
        for phase, stage in expected.items():
            with self.subTest(phase=phase):
                self.assertEqual(stage, stage_for_status(self.status(phase))[0])

    def test_reviewed_uses_recorded_next_action_reason_precedence(self) -> None:
        cases = (
            ("重大問題または要求未達が残っています", "指摘別の修正計画を準備してください", "修正"),
            ("必要な動作確認が未完了です", "不足する必須確認を依頼してください", "QA・確認"),
            ("PASS以外の結果から終了候補には進めません", "結論を確認してください", "QA・確認"),
            ("技術的な終了候補です。自動受入は行いません", "残余事項を確認して終了判断を指示してください", "判断待ち"),
        )
        for reason, action, stage in cases:
            with self.subTest(reason=reason):
                self.assertEqual(stage, stage_for_status(self.status("reviewed", reason=reason, action=action))[0])

    def test_publication_refusal_precedes_the_general_phase(self) -> None:
        result = self.status("prepared", reason="最終公開走査で拒否されました。既存の依頼と状態は保持されています")
        self.assertEqual("判断待ち", stage_for_status(result)[0])
        self.assertIn("停止", stage_for_status(result)[1])

    def test_unknown_phase_is_not_reported_as_success_or_terminal(self) -> None:
        stage, detail = stage_for_status(self.status("unexpected-phase"))
        self.assertEqual("未定義", stage)
        self.assertIn("unexpected-phase", detail)
        self.assertNotEqual("終了", stage)

    def test_pending_correction_precedes_acquired_content_phase(self) -> None:
        status = self.status("content_pending", reason="取得・構造確認は意味の妥当性を証明しません", action="訂正依頼文を渡してください")
        stage, detail = stage_for_status(status, pending_correction=True)
        self.assertEqual("QA・確認", stage)
        self.assertIn("停止", detail)
        self.assertIn("訂正待ち", detail)
        self.assertNotIn("妥当性を確認待ち", detail)
        output = render_status(status, pending_correction=True)
        self.assertIn("操作: 訂正依頼文を渡してください", output)
        self.assertIn("詳細: 停止", output)

    def test_invitation_and_every_issue_are_retained_in_both_languages(self) -> None:
        status = self.status("invalid")
        status["next"]["依頼文"] = "# 訂正依頼\n不足している根拠を提出してください。"
        status["issues"] = [f"必須項目{index}が不足" for index in range(50)]
        for lang in ("ja", "en"):
            with self.subTest(lang=lang):
                output = render_status(status, lang=lang)
                self.assertIn("渡す文書:\n" + status["next"]["依頼文"], output)
                self.assertEqual(50, output.count("確認事項: "))
                for issue in status["issues"]:
                    self.assertIn("確認事項: " + issue, output)

    def test_rendering_does_not_mutate_status_and_keeps_legacy_codes_in_english(self) -> None:
        status = self.status("content_pending", reason="妥当性確認待ち")
        before = {key: value.copy() if isinstance(value, dict) else value for key, value in status.items()}
        ja = render_status(status)
        en = render_status(status, lang="en")
        self.assertIn("工程 QA・確認", ja)
        self.assertIn("状況 content_pending", en)
        self.assertEqual(before, status)

    def test_invalid_language_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "jaまたはen"):
            render_status(self.status("prepared"), lang="fr")

    @staticmethod
    def reviewed_state(request_id: str, cycle: int, sha: str, gate: str) -> dict:
        active_hash = (gate.lower() + "0" * 64)[:64]
        return {
            "id": request_id,
            "cycle": cycle,
            "phase": "reviewed",
            "reviewed": sha,
            "active_review": active_hash,
            "pending_correction": None,
            "reviews": [{
                "hash": active_hash,
                "content_checked": True,
                "issues": [],
                "parsed": {"gate": gate},
            }],
        }

    def test_all_four_recorded_gates_keep_distinct_japanese_labels(self) -> None:
        self.assertEqual(4, len(QA_GATE_LABELS))
        self.assertEqual(
            {"PASS": "基準充足", "FAIL": "基準未達", "HOLD": "保留", "INCONCLUSIVE": "判定不能"},
            QA_GATE_LABELS,
        )
        for gate, label in QA_GATE_LABELS.items():
            with self.subTest(gate=gate):
                record = assessment_from_state(
                    self.reviewed_state("QA-0001", 3, "a" * 40, gate)
                )
                self.assertEqual(gate, record["gate"])
                output = render_status(
                    self.status("reviewed"), current_assessment=record
                )
                self.assertIn(label, output)
                self.assertIn(gate, output)
                self.assertIn("a" * 40, output)
                self.assertIn("サイクル 3", output)

    def test_current_result_and_previous_cycle_result_are_separate(self) -> None:
        old = self.reviewed_state("QA-0001", 1, "b" * 40, "PASS")
        middle = {"id": "QA-0002", "cycle": 2, "phase": "prepared", "previous": "QA-0001"}
        current = {
            **self.reviewed_state("QA-0003", 3, "c" * 40, "HOLD"),
            "previous": "QA-0002",
        }
        current_record, previous_record = resolve_assessments(
            current, {"QA-0001": old, "QA-0002": middle}.__getitem__
        )
        output = render_status(
            self.status("reviewed"),
            current_assessment=current_record,
            previous_assessment=previous_record,
        )
        self.assertIn("現在サイクルのQA判定: 保留（HOLD）", output)
        self.assertIn("対象版 " + "c" * 40 + "／サイクル 3", output)
        self.assertIn("過去のQA判定: 基準充足（PASS）", output)
        self.assertIn("対象版 " + "b" * 40 + "／サイクル 1 ／ 依頼 QA-0001", output)

    def test_no_current_result_does_not_relabel_historical_gate_as_current(self) -> None:
        current = {
            "id": "QA-0002",
            "cycle": 2,
            "phase": "prepared",
            "reviewed": "d" * 40,
            "active_review": None,
            "pending_correction": None,
            "reviews": [],
            "previous": "QA-0001",
        }
        old = self.reviewed_state("QA-0001", 1, "b" * 40, "FAIL")
        current_record, previous_record = resolve_assessments(
            current, {"QA-0001": old}.__getitem__
        )
        output = render_status(
            {"id": current["id"], "cycle": current["cycle"], "phase": current["phase"], "reviewed": current["reviewed"], "next": {}},
            current_assessment=current_record,
            previous_assessment=previous_record,
        )
        self.assertIsNone(current_record)
        self.assertIn("現在サイクルのQA判定: なし（未記録）", output)
        self.assertIn("過去のQA判定: 基準未達（FAIL）", output)
        self.assertNotIn("現在サイクルのQA判定: 基準未達", output)
        self.assertIn("評価対象版: " + "d" * 40, output)

    def test_unconfirmed_or_corrected_review_is_not_a_current_result(self) -> None:
        state = self.reviewed_state("QA-0001", 1, "a" * 40, "PASS")
        state["reviews"][0]["content_checked"] = False
        self.assertIsNone(assessment_from_state(state))
        state["reviews"][0]["content_checked"] = True
        state["pending_correction"] = {"correction_id": "QA-0001-C001"}
        self.assertIsNone(assessment_from_state(state))

    def test_recorded_result_remains_separate_during_plan_repair_and_reqa_handoff(self) -> None:
        for phase in ("reviewed", "planned", "approved", "submitted", "decision"):
            with self.subTest(phase=phase):
                state = self.reviewed_state("QA-0001", 1, "a" * 40, "FAIL")
                state["phase"] = phase
                self.assertEqual("FAIL", assessment_from_state(state)["gate"])


if __name__ == "__main__":
    unittest.main()
