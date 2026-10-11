from __future__ import annotations

import unittest
from quality_loop.markdown_report import generate_resume_markdown, determine_traffic_light, generate_action_guide


class MarkdownReportTest(unittest.TestCase):
    def test_resume_traffic_light_red_for_blocking_finding(self) -> None:
        """未解決のblocking Findingがある場合は赤信号"""
        case = {
            "case_metadata": {
                "case_id": "QMS-0001",
                "revision": 2,
                "status": "implementer-action",
                "owner": "owner-001",
                "cycle_count": 1,
                "cycle_limit": 3,
            },
            "baseline": {
                "purpose": "品質確認",
                "requirements": [{"requirement_id": "REQ-001", "text": "正常動作"}],
                "targets": ["src/app.py"],
            },
            "implementation_authorization": {"allowed": True, "finding_ids": ["F-001"], "allowed_targets": ["src/app.py"]},
            "findings": [
                {
                    "finding_id": "F-001",
                    "classification": "requirement-violation",
                    "severity": "high",
                    "requirement_ref": "REQ-001",
                    "observed_fact": "不具合発生",
                    "status": "open",
                }
            ],
            "events": [{"operation": "review", "role": "reviewer", "case_revision": 2}],
            "handoff": {
                "handoff_id": "hnd-001",
                "issued_revision": 2,
                "next_role": "implementer",
                "next_action": "submit-response",
            },
        }
        report = generate_resume_markdown(case)
        self.assertIn("🔴", report)
        self.assertIn("要対応", report)
        self.assertIn("python3 -B -m quality_loop.cli submit-response", report)

    def test_resume_traffic_light_red_for_held_status(self) -> None:
        """status == held 単体で赤信号"""
        color, reason = determine_traffic_light(
            status="held",
            cycle_count=0,
            cycle_limit=3,
            blocking_findings=[],
            gap_findings=[],
        )
        self.assertIn("🔴", color)
        self.assertIn("保留(held)", reason)

    def test_resume_traffic_light_red_for_requires_rereview_status(self) -> None:
        """status == requires-rereview 単体で赤信号"""
        color, reason = determine_traffic_light(
            status="requires-rereview",
            cycle_count=0,
            cycle_limit=3,
            blocking_findings=[],
            gap_findings=[],
        )
        self.assertIn("🔴", color)
        self.assertIn("再レビューが必要", reason)

    def test_resume_traffic_light_red_for_cycle_limit_reached(self) -> None:
        """cycle_count >= cycle_limit で赤信号"""
        color, reason = determine_traffic_light(
            status="implementer-action",
            cycle_count=3,
            cycle_limit=3,
            blocking_findings=[],
            gap_findings=[],
        )
        self.assertIn("🔴", color)
        self.assertIn("サイクル上限(3)に到達", reason)

    def test_resume_traffic_light_red_multiple_reasons_combined(self) -> None:
        """複数の赤条件が重なった場合に理由が結合される"""
        color, reason = determine_traffic_light(
            status="held",
            cycle_count=3,
            cycle_limit=3,
            blocking_findings=[{"finding_id": "F-001"}],
            gap_findings=[],
        )
        self.assertIn("🔴", color)
        self.assertIn("保留(held)", reason)
        self.assertIn("サイクル上限", reason)
        self.assertIn("未解決の重要課題が 1 件", reason)

    def test_resume_traffic_light_yellow_for_evidence_gap(self) -> None:
        """blockingがなくevidence-gapのみの場合は黄信号"""
        case = {
            "case_metadata": {
                "case_id": "QMS-0002",
                "revision": 4,
                "status": "owner-adjudication",
                "owner": "owner-001",
                "cycle_count": 1,
                "cycle_limit": 3,
            },
            "baseline": {
                "purpose": "外部検証",
                "requirements": [{"requirement_id": "REQ-001", "text": "実機負荷テスト"}],
                "targets": ["src/app.py"],
            },
            "implementation_authorization": {"allowed": False, "finding_ids": [], "allowed_targets": []},
            "findings": [
                {
                    "finding_id": "F-GAP-01",
                    "classification": "evidence-gap",
                    "severity": "low",
                    "requirement_ref": "REQ-001",
                    "observed_fact": "実機クラスタ未接続",
                    "status": "open",
                }
            ],
            "events": [
                {"operation": "create-case", "role": "owner", "case_revision": 1},
                {"operation": "review", "role": "reviewer", "case_revision": 2},
                {"operation": "verify", "role": "reviewer", "case_revision": 4},
            ],
            "handoff": {
                "handoff_id": "hnd-002",
                "issued_revision": 4,
                "next_role": "owner",
                "next_action": "adjudicate",
            },
        }
        report = generate_resume_markdown(case)
        self.assertIn("🟡", report)
        self.assertIn("条件付き", report)
        self.assertIn("adjudicate_risk_dry_run.json", report)

    def test_resume_traffic_light_green_proposal_only(self) -> None:
        """blockingがなくimprovement-proposalのみの場合は緑信号"""
        case = {
            "case_metadata": {
                "case_id": "QMS-PROP-01",
                "revision": 2,
                "case_id": "QMS-0003",
                "revision": 4,
                "status": "owner-adjudication",
                "owner": "owner-001",
                "cycle_count": 1,
                "cycle_limit": 3,
            },
            "baseline": {
                "purpose": "品質向上",
                "requirements": [{"requirement_id": "REQ-001", "text": "正常動作"}],
                "targets": ["src/app.py"],
            },
            "implementation_authorization": {"allowed": False, "finding_ids": [], "allowed_targets": []},
            "findings": [
                {
                    "finding_id": "F-PROP-01",
                    "classification": "improvement-proposal",
                    "severity": "low",
                    "requirement_ref": "REQ-001",
                    "observed_fact": "リファクタリング可能",
                    "status": "open",
                }
            ],
            "events": [
                {"operation": "create-case", "role": "owner", "case_revision": 1},
                {"operation": "review", "role": "reviewer", "case_revision": 2},
                {"operation": "verify", "role": "reviewer", "case_revision": 4},
            ],
            "handoff": {
                "handoff_id": "hnd-003",
                "issued_revision": 4,
                "next_role": "owner",
                "next_action": "adjudicate",
            },
        }
        report = generate_resume_markdown(case)
        self.assertIn("🟢", report)
        self.assertIn("検証完了", report)

    def test_resume_traffic_light_green_and_handoff_command(self) -> None:
        """全件verifiedの場合は緑信号、Owner裁定待ちでdry-run案内"""
        case = {
            "case_metadata": {
                "case_id": "QMS-0004",
                "revision": 4,
                "status": "owner-adjudication",
                "owner": "owner-001",
                "cycle_count": 1,
                "cycle_limit": 3,
            },
            "baseline": {
                "purpose": "品質向上",
                "requirements": [{"requirement_id": "REQ-001", "text": "正常動作"}],
                "targets": ["src/app.py"],
            },
            "implementation_authorization": {"allowed": False, "finding_ids": [], "allowed_targets": []},
            "findings": [
                {
                    "finding_id": "F-001",
                    "classification": "requirement-violation",
                    "severity": "high",
                    "requirement_ref": "REQ-001",
                    "observed_fact": "修正完了",
                    "status": "verified",
                },
                {
                    "finding_id": "PROP-001",
                    "classification": "improvement-proposal",
                    "severity": "low",
                    "requirement_ref": "REQ-001",
                    "observed_fact": "型ヒント追加推奨",
                    "status": "open",
                },
            ],
            "events": [
                {"operation": "create-case", "role": "owner", "case_revision": 1},
                {"operation": "review", "role": "reviewer", "case_revision": 2},
                {"operation": "verify", "role": "reviewer", "case_revision": 4},
            ],
            "handoff": {
                "handoff_id": "hnd-004",
                "issued_revision": 4,
                "next_role": "owner",
                "next_action": "adjudicate",
            },
        }
        report = generate_resume_markdown(case)
        self.assertIn("🟢", report)
        self.assertIn("検証完了", report)
        self.assertIn("python3 -B -m quality_loop.cli adjudicate", report)
        self.assertIn("dry_run", report)
        self.assertIn("confirm", report)
        self.assertIn("改善提案（次回以降への引き継ぎ事項）", report)
        self.assertIn("PROP-001", report)

    def test_action_guide_for_reviewer_roles(self) -> None:
        """Reviewerロール（review, verify）に対するCLI案内"""
        lines_review = generate_action_guide(
            case_id="QMS-REV-01",
            next_role="reviewer",
            next_action="review",
            handoff_id="hnd-r-01",
            traffic_color="🟢",
        )
        self.assertTrue(any("python3 -B -m quality_loop.cli review" in l for l in lines_review))

        lines_verify = generate_action_guide(
            case_id="QMS-REV-02",
            next_role="reviewer",
            next_action="verify",
            handoff_id="hnd-r-02",
            traffic_color="🔴",
        )
        self.assertTrue(any("python3 -B -m quality_loop.cli verify" in l for l in lines_verify))

    def test_action_guide_terminal_state_no_commands(self) -> None:
        """終端状態（next_roleなし）ではCLIコマンドが出力されない"""
        lines = generate_action_guide(
            case_id="QMS-TERM-01",
            next_role=None,
            next_action=None,
            handoff_id="none",
            traffic_color="🟢",
        )
        self.assertIn("- この案件は終端状態に達しており、追加の操作は不要です。", lines)
        self.assertFalse(any("```bash" in l for l in lines))

    def test_resume_action_guide_commands_are_executable_by_cli_parser(self) -> None:
        """P0-1: action guideが生成する全CLIコマンドが実CLI引数パーサーで正常に解釈される"""
        from quality_loop.cli import build_parser

        parser = build_parser()
        lines = generate_action_guide(
            case_id="QMS-EXEC-01",
            next_role="owner",
            next_action="adjudicate",
            handoff_id="hnd-exec-01",
            traffic_color="🟢",
            revision=2,
        )
        for line in lines:
            if line.strip().startswith("python3 -B -m quality_loop.cli "):
                cmd_tokens = line.strip().split()[4:]  # skip python3 -B -m quality_loop.cli
                args = parser.parse_args(cmd_tokens)
                self.assertEqual("adjudicate", args.command)
                self.assertEqual("QMS-EXEC-01", args.case_id)
                self.assertTrue(args.input.endswith(".json"))

    def test_terminal_accepted_is_always_green_even_if_cycle_limit_reached(self) -> None:
        """P0-2: cycle_limit (3/3) に到達していても、Owner最終裁定が accepted であれば緑信号になる"""
        color, reason = determine_traffic_light(
            status="accepted",
            cycle_count=3,
            cycle_limit=3,
            blocking_findings=[],
            gap_findings=[],
            has_reviewed=True,
        )
        self.assertIn("🟢", color)
        self.assertIn("Owner受入確定", color)
        self.assertNotIn("安全", color)
        self.assertIn("安全性の追加保証を意味しません", reason)
        self.assertNotIn("🔴", color)

    def test_terminal_accepted_with_risk_is_yellow_not_red(self) -> None:
        """P0-2: cycle_limit (3/3) に到達していても、accepted-with-risk であれば黄信号になる"""
        color, reason = determine_traffic_light(
            status="accepted-with-risk",
            cycle_count=3,
            cycle_limit=3,
            blocking_findings=[],
            gap_findings=[],
            has_reviewed=True,
        )
        self.assertIn("🟡", color)
        self.assertIn("残余リスク付き受入確定", color)
        self.assertIn("残余リスクを受容しました", reason)
        self.assertNotIn("🔴", color)

    def test_resume_markdown_localizes_stage_handoff_and_reviewer_recommendation(self) -> None:
        case = {
            "case_metadata": {
                "case_id": "QMS-RESUME-01",
                "revision": 5,
                "status": "reviewer-final-assessment",
                "owner": "owner-001",
                "cycle_count": 3,
                "cycle_limit": 3,
                "last_operation": "verify",
            },
            "baseline": {
                "purpose": "残余課題の評価",
                "targets": ["src/app.py"],
                "target_revision": "reviewed-v5",
            },
            "implementation_authorization": {"allowed": False, "allowed_targets": []},
            "findings": [
                {
                    "finding_id": "F-GAP-01",
                    "classification": "evidence-gap",
                    "severity": "medium",
                    "observed_fact": "実機確認が未実施",
                    "required_evidence": "実機ログ",
                    "status": "unverified",
                }
            ],
            "verifications": [
                {"finding_id": "F-GAP-01", "result": "unverified", "verification_revision": 5}
            ],
            "final_risk_assessments": [
                {"revision": 5, "overall_recommendation": "defer", "rationale": "実機確認が必要", "residual_risks": []}
            ],
            "events": [{"operation": "review"}],
            "handoff": {
                "handoff_id": "hnd-resume-01",
                "next_role": "reviewer",
                "next_action": "assess-risk",
            },
        }
        report = generate_resume_markdown(case)
        self.assertIn("現在の状態**: reviewer-final-assessment（QA・確認）", report)
        self.assertIn("評価対象版 (baseline.target_revision)**: `reviewed-v5`", report)
        self.assertIn("次の担当**: レビュー担当（reviewer）", report)
        self.assertIn("次の操作**: 残余リスクの最終評価（assess-risk）", report)
        self.assertIn("Reviewer評価勧告**: 判断延期推奨（defer）", report)
        self.assertIn("状態: 未検証 (`unverified`)", report)

        case["case_metadata"]["revision"] = 6
        case["baseline"]["target_revision"] = "fixed-v6"
        report = generate_resume_markdown(case)
        self.assertIn("Reviewer評価勧告**: 未記録（現在版）。過去評価（case Revision 5", report)
        self.assertIn("対象版・サイクル未特定）: 判断延期推奨（defer）", report)

    def test_resume_markdown_distinguishes_owner_terminal_and_held_decisions(self) -> None:
        cases = (
            (
                "accepted",
                {"decision": "accepted", "rationale": "全件を確認"},
                "Ownerが受入を確定",
                "安全性の追加保証を意味しません",
            ),
            (
                "accepted-with-risk",
                {
                    "decision": "accepted-with-risk",
                    "rationale": "条件を設定して受容",
                    "conditions": ["月次で監視"],
                    "residual_risks": [{"finding_id": "F-RISK-01"}],
                },
                "残余リスク付き受入確定（accepted-with-risk）",
                "条件付き受入はリスク解消を意味しません",
            ),
            (
                "rejected",
                {"decision": "rejected", "rationale": "要件を満たせない"},
                "却下確定（rejected）",
                "QA GateのFAILとは別の判断です",
            ),
            (
                "held",
                {"decision": "held", "rationale": "追加Evidenceが必要"},
                "保留中（held）",
                "案件は停止中です",
            ),
        )
        for state, decision, expected_decision, detail in cases:
            with self.subTest(state=state):
                is_held = state == "held"
                case = {
                    "case_metadata": {
                        "case_id": f"QMS-{state}",
                        "revision": 6,
                        "status": state,
                        "owner": "owner-001",
                        "cycle_count": 2,
                        "cycle_limit": 3,
                    },
                    "baseline": {"purpose": "判断の確認", "targets": ["src/app.py"]},
                    "implementation_authorization": {"allowed": False, "allowed_targets": []},
                    "findings": [],
                    "events": [{"operation": "review"}],
                    "handoff": {
                        "handoff_id": f"hnd-{state}",
                        "next_role": "owner" if is_held else None,
                        "next_action": "adjudicate" if is_held else None,
                    },
                    "adjudications": [decision],
                }
                report = generate_resume_markdown(case)
                self.assertIn(expected_decision, report)
                self.assertIn(detail, report)
                self.assertIn("状態**: " + state + "（" + ("判断待ち" if is_held else "終了") + "）", report)

    def test_unknown_resume_status_is_not_reported_as_verified_or_safe(self) -> None:
        color, reason = determine_traffic_light(
            status="future-status",
            cycle_count=0,
            cycle_limit=3,
            blocking_findings=[],
            gap_findings=[],
            has_reviewed=True,
        )
        self.assertIn("未定義", color)
        self.assertIn("工程を特定できません", reason)
        self.assertNotIn("安全", color)

    def test_final_risk_assessment_markdown_renders_all_material_fields(self) -> None:
        """P0-5: final-risk-assessment.md が controls, assumptions, alternatives, proportionality, triggers を網羅表示する"""
        from quality_loop.markdown_report import generate_final_risk_assessment_markdown

        case = {
            "case_metadata": {
                "case_id": "QMS-RISK-01",
                "revision": 5,
                "status": "reviewer-final-assessment",
                "cycle_count": 2,
                "cycle_limit": 3,
            },
            "baseline": {"target_revision": "reviewed-v5"},
            "findings": [
                {
                    "finding_id": "F-001",
                    "classification": "evidence-gap",
                    "severity": "medium",
                    "observed_fact": "外部連携テスト未完",
                    "status": "unverified",
                }
            ],
            "final_risk_assessments": [
                {
                    "revision": 5,
                    "overall_recommendation": "accept-with-conditions",
                    "rationale": "十分なフォールバックがあるため条件付き受入を推奨",
                    "residual_risks": [
                        {
                            "finding_id": "F-001",
                            "current_status": "unverified",
                            "severity": "medium",
                            "implemented_controls": ["リトライ機能 (3回)", "タイムアウト監視 (10秒)"],
                            "residual_risk_description": "ネットワーク瞬断時の遅延リスク",
                            "assumptions_supporting_acceptance": ["本番回線がSLA 99.9%を満たすこと"],
                            "likelihood": "low",
                            "impact": "low",
                            "alternatives": ["非同期キュー導入", "オフラインバッファ"],
                            "proportionality_assessment": "これ以上の追加検証は費用対効果が低い",
                            "qa_recommendation": "accept-with-conditions",
                            "confidence": "high",
                            "reassessment_triggers": ["遅延アラートが月3回以上発生時"],
                        }
                    ],
                }
            ],
        }

        report = generate_final_risk_assessment_markdown(case)
        self.assertIn("評価結果の対象版・サイクル**: `reviewed-v5` / 2/3", report)
        self.assertNotIn("現在の対象に対する評価**: 未記録", report)
        self.assertIn("実装済み対策 (Implemented Controls)", report)
        self.assertIn("リトライ機能 (3回)", report)
        self.assertIn("受入前提条件 (Acceptance Assumptions)", report)
        self.assertIn("本番回線がSLA 99.9%を満たすこと", report)
        self.assertIn("代替策・選択肢 (Alternatives)", report)
        self.assertIn("非同期キュー導入", report)
        self.assertIn("比例性・妥当性評価 (Proportionality)", report)
        self.assertIn("これ以上の追加検証は費用対効果が低い", report)
        self.assertIn("再評価トリガー (Reassessment Triggers)", report)
        self.assertIn("遅延アラートが月3回以上発生時", report)

    def test_final_risk_assessment_marks_stale_result_as_historical(self) -> None:
        from quality_loop.markdown_report import generate_final_risk_assessment_markdown

        case = {
            "case_metadata": {
                "case_id": "QMS-RISK-HISTORY",
                "revision": 6,
                "status": "reviewer-action",
                "cycle_count": 3,
                "cycle_limit": 4,
            },
            "baseline": {"target_revision": "fixed-v6"},
            "findings": [],
            "final_risk_assessments": [
                {
                    "revision": 5,
                    "overall_recommendation": "defer",
                    "rationale": "過去の評価",
                    "residual_risks": [],
                }
            ],
        }

        report = generate_final_risk_assessment_markdown(case)
        self.assertIn("過去評価（case Revision 5）", report)
        self.assertIn("評価結果の対象版・サイクル**: 過去評価の対象は特定不能", report)
        self.assertIn(
            "現在の対象に対する評価**: 未記録（case Revision 6、対象版 `fixed-v6`、サイクル 3/4）",
            report,
        )


if __name__ == "__main__":
    unittest.main()
