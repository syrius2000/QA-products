from __future__ import annotations

from typing import Any

from .status_display import (
    ACTION_LABELS,
    CASE_STATUS_STAGES,
    FINDING_RESULT_LABELS,
    RECOMMENDATION_LABELS,
    ROLE_LABELS,
    risk_recommendation_display,
)


OWNER_DECISION_LABELS = {
    "accepted": "受入確定",
    "accepted-with-risk": "残余リスク付き受入確定",
    "rework-requested": "再作業指示",
    "held": "保留中",
    "rejected": "却下確定",
}

OPERATION_LABELS = {
    "create-case": "案件作成",
    "review": "レビュー",
    "submit-plan": "修正計画提出",
    "review-plan": "修正計画審査",
    "submit-response": "Finding別回答提出",
    "verify": "独立検証",
    "assess-risk": "最終リスク評価",
    "adjudicate": "Owner裁定",
}


def determine_traffic_light(
    *,
    status: str,
    cycle_count: int,
    cycle_limit: int,
    blocking_findings: list[dict[str, Any]],
    gap_findings: list[dict[str, Any]],
    has_reviewed: bool = True,
) -> tuple[str, str]:
    """
    信号機判定（決定論的優先順位:
    1. 赤: 保留/再レビュー/却下/サイクル上限/未解決blocking Findingあり
    2. 白: 初回レビュー未実施 (案件作成直後)
    3. 黄: 観測限界 (evidence-gap) / 残余リスク受容 / 最終リスク評価中
    4. 青: 修正・検証進行中 (blockingなし・gapなし)
    5. 緑: 技術検証完了・Owner裁定待ち（安全性や受入の保証ではない）
    ）
    """
    # 1. 終端状態 (Owner最終裁定) を最優先
    if status == "accepted":
        return "🟢 緑 (Owner受入確定) [Owner裁定: accepted]", "Ownerが受入を確定しました。この表示は安全性の追加保証を意味しません"
    if status == "accepted-with-risk":
        return "🟡 黄 (残余リスク付き受入確定) [Owner裁定: accepted-with-risk]", "Ownerが明示された条件の下で残余リスクを受容しました。リスクと再評価条件は残ります"
    if status == "rejected":
        return "🔴 赤 (Owner却下確定) [Owner裁定: rejected]", "Ownerが案件を却下しました。これはQA GateのFAILとは別のOwner裁定です"

    # 2. 未レビュー状態 (案件作成直後 / 初回レビュー待ち)
    if not has_reviewed or status == "created":
        return "⚪ 白 (未評価・初回レビュー待ち)", "案件作成済みですが、Reviewerによる初回評価が未実施です"

    # 3. 未解決の重要課題 / 基準変更再レビュー / サイクル上限到達 / 保留 (非終端時)
    if (
        status in ("held", "requires-rereview")
        or len(blocking_findings) > 0
        or cycle_count >= cycle_limit
    ):
        reasons: list[str] = []
        if status == "held":
            reasons.append("案件が保留(held)されています（再開にはOwnerによるadjudicateが必要です）")
        if status == "requires-rereview":
            reasons.append("基準変更に伴う再レビューが必要です")
        if blocking_findings:
            reasons.append(f"未解決の重要課題が {len(blocking_findings)} 件あります")
        if cycle_count >= cycle_limit:
            reasons.append(f"サイクル上限({cycle_limit})に到達しています（Reviewerによる最終リスク評価またはOwner裁定が必要です）")

        return "🔴 赤 (要対応・確認待ち)", " / ".join(reasons) or "要対応事項があります"

    # 4. 黄信号 (観測限界 / 最終リスク評価中)
    if len(gap_findings) > 0 or status == "reviewer-final-assessment":
        if status == "reviewer-final-assessment":
            return "🟡 黄 (最終リスク評価中)", "サイクル上限または残余リスクに伴い、ReviewerによるFinal Risk Assessmentを実施中です"
        return "🟡 黄 (条件付き・外部制約あり)", f"観測限界(evidence-gap)が {len(gap_findings)} 件あります"

    if status == "reviewer-action":
        return "⚪ 白 (基準変更後の再レビュー待ち)", "更新された基準に対するReviewerの再レビューが必要です"

    # 5. 進行中状態 (Plan策定中 / 実装中 / 再検証中)
    if status in ("implementer-plan", "reviewer-plan-review", "implementer-action", "reviewer-verification"):
        return "🔵 青 (評価・修正進行中)", f"現在 {status} 工程が進行中です（検証完了前）"

    # 6. 技術検証完了後のOwner裁定待ち
    if status == "owner-adjudication":
        return "🟢 緑 (技術検証完了・Owner裁定待ち)", "未解決の阻害Findingはありません。Owner裁定と受入はまだ確定していません"

    return "⚪ 白 (未定義の状態)", f"状態 {status!r} の工程を特定できません。状態記録を確認してください"


def generate_action_guide(
    *,
    case_id: str,
    next_role: str | None,
    next_action: str | None,
    handoff_id: str,
    traffic_color: str,
    revision: int = 1,
) -> list[str]:
    lines: list[str] = ["## 4. 次の一手 (Handoff ガイド)"]
    if (
        not next_role
        or not next_action
        or next_role in ("none", "なし (終端)", None)
        or next_action in ("none", "なし (終端)", None)
    ):
        lines.append("- この案件は終端状態に達しており、追加の操作は不要です。")
        return lines

    lines.append(f"- **次の担当**: `{next_role}`")
    lines.append(f"- **実行すべき操作**: `{next_action}`")
    lines.append(f"- **参照Handoff ID**: `{handoff_id}`")
    lines.append("")
    lines.append("### AI/Operator向け実行コマンド例 (入力ファイル方式):")

    if next_role == "owner" and next_action == "adjudicate":
        if "🟢" in traffic_color:
            lines.append("1. **事前確認 (dry-run)**:")
            lines.append(f"   ```bash\n   python3 -B -m quality_loop.cli adjudicate --case-id {case_id} --input adjudicate_dry_run.json\n   ```")
            lines.append("2. **受入本承認 (confirm)**:")
            lines.append(f"   ```bash\n   python3 -B -m quality_loop.cli adjudicate --case-id {case_id} --input adjudicate_confirm.json\n   ```")
        elif "🟡" in traffic_color:
            lines.append("1. **残余リスク付き受入 (事前dry-run)**:")
            lines.append(f"   ```bash\n   python3 -B -m quality_loop.cli adjudicate --case-id {case_id} --input adjudicate_risk_dry_run.json\n   ```")
            lines.append("2. **残余リスク付き受入 (本承認)**:")
            lines.append(f"   ```bash\n   python3 -B -m quality_loop.cli adjudicate --case-id {case_id} --input adjudicate_risk_confirm.json\n   ```")
            lines.append("3. **再修正の指示 (追加サイクル付与)**:")
            lines.append(f"   ```bash\n   python3 -B -m quality_loop.cli adjudicate --case-id {case_id} --input rework.json\n   ```")
        else:
            lines.append("1. **再作業指示 (追加サイクル付与)**:")
            lines.append(f"   ```bash\n   python3 -B -m quality_loop.cli adjudicate --case-id {case_id} --input rework.json\n   ```")
            lines.append("2. **案件の保留 (held)**:")
            lines.append(f"   ```bash\n   python3 -B -m quality_loop.cli adjudicate --case-id {case_id} --input hold.json\n   ```")
            lines.append("3. **案件の却下 (rejected)**:")
            lines.append(f"   ```bash\n   python3 -B -m quality_loop.cli adjudicate --case-id {case_id} --input reject.json\n   ```")
    elif next_role == "reviewer" and next_action == "assess-risk":
        lines.append(f"```bash\npython3 -B -m quality_loop.cli assess-risk --case-id {case_id} --input assess_risk.json\n```")
    elif next_role == "implementer" and next_action == "submit-plan":
        lines.append(f"```bash\npython3 -B -m quality_loop.cli submit-plan --case-id {case_id} --input plan.json\n```")
    elif next_role == "reviewer" and next_action == "review-plan":
        lines.append(f"```bash\npython3 -B -m quality_loop.cli review-plan --case-id {case_id} --input plan_review.json\n```")
    elif next_role == "implementer" and next_action == "submit-response":
        lines.append(f"```bash\npython3 -B -m quality_loop.cli submit-response --case-id {case_id} --input response.json\n```")
    elif next_role == "reviewer" and next_action == "verify":
        lines.append(f"```bash\npython3 -B -m quality_loop.cli verify --case-id {case_id} --input verify.json\n```")
    elif next_role == "reviewer" and next_action == "review":
        lines.append(f"```bash\npython3 -B -m quality_loop.cli review --case-id {case_id} --input review.json\n```")
    else:
        lines.append(f"```bash\npython3 -B -m quality_loop.cli {next_action} --case-id {case_id} --input input.json\n```")

    return lines


def generate_resume_markdown(case: dict[str, Any]) -> str:
    meta = case.get("case_metadata", {})
    case_id = meta.get("case_id", "UNKNOWN")
    # 正本フィールド revision を優先し、後方互換で case_revision をフォールバック
    rev = meta.get("revision", meta.get("case_revision", 1))
    status = meta.get("status", "unknown")
    owner = meta.get("owner", "unknown")
    stage, stage_detail = CASE_STATUS_STAGES.get(
        status, ("未定義", f"状態 {status!r} の工程を特定できません")
    )
    cycle_count = meta.get("cycle_count", 0)
    cycle_limit = meta.get("cycle_limit", 3)

    baseline = case.get("baseline", {})
    purpose = baseline.get("purpose", "")
    targets = baseline.get("targets", [])
    target_revision = baseline.get("target_revision")
    target_revision_display = f"`{target_revision}`" if target_revision else "未特定"

    auth = case.get("implementation_authorization", {})
    auth_allowed = auth.get("allowed", False)
    auth_targets = ", ".join(f"`{t}`" for t in auth.get("allowed_targets", [])) or "なし"

    handoff = case.get("handoff", {})
    next_role_code = handoff.get("next_role")
    next_action_code = handoff.get("next_action")
    next_role = next_role_code or "なし (終端)"
    next_action = next_action_code or "なし (終端)"
    next_role_display = (
        f"{ROLE_LABELS.get(next_role_code, '未定義')}（{next_role_code}）"
        if next_role_code
        else "なし（終端）"
    )
    next_action_display = (
        f"{ACTION_LABELS.get(next_action_code, '未定義')}（{next_action_code}）"
        if next_action_code
        else "なし（終端）"
    )
    handoff_id = handoff.get("handoff_id", "none")
    last_op = meta.get("last_operation", "なし")
    last_op_display = (
        f"{OPERATION_LABELS.get(last_op, '未定義')}（{last_op}）"
        if last_op != "なし"
        else "なし"
    )

    findings = case.get("findings", [])
    from .model import RESOLVED_VERIFICATION_RESULTS
    blocking_findings = [
        f
        for f in findings
        if f.get("status") not in RESOLVED_VERIFICATION_RESULTS
        and f.get("classification") in ("requirement-violation", "regression", "purpose-risk")
    ]
    gap_findings = [
        f
        for f in findings
        if f.get("status") not in RESOLVED_VERIFICATION_RESULTS and f.get("classification") == "evidence-gap"
    ]
    proposals = [f for f in findings if f.get("classification") == "improvement-proposal"]
    recommendation_display = risk_recommendation_display(case)
    adjudications = case.get("adjudications", [])
    latest_adjudication = adjudications[-1] if adjudications else None
    owner_decision = latest_adjudication.get("decision") if latest_adjudication else None
    owner_decision_display = (
        f"{OWNER_DECISION_LABELS.get(owner_decision, '未定義')}（{owner_decision}）"
        if owner_decision
        else "未記録"
    )

    events = case.get("events", [])
    has_reviewed = any(e.get("operation") == "review" for e in events)

    traffic_color, traffic_reason = determine_traffic_light(
        status=status,
        cycle_count=cycle_count,
        cycle_limit=cycle_limit,
        blocking_findings=blocking_findings,
        gap_findings=gap_findings,
        has_reviewed=has_reviewed,
    )

    lines: list[str] = [
        f"# 案件ステータス要約: {case_id} (Revision {rev})",
        "",
        f"### **総合状況**: {traffic_color}",
        f"> **理由・診断**: {traffic_reason}",
        "",
        "---",
        "",
        "## 1. 基本情報 & ガードレール状況",
        f"- **現在の状態**: {status}（{stage}）",
        f"- **状態の詳細**: {stage_detail}",
        f"- **評価対象版 (baseline.target_revision)**: {target_revision_display}",
        f"- **サイクル**: {cycle_count}/{cycle_limit}",
        f"- **Owner (統括者)**: {owner}",
        f"- **最後の完了操作**: {last_op_display}",
        f"- **次の担当**: {next_role_display}",
        f"- **次の操作**: {next_action_display}",
        f"- **最新Handoff ID**: `{handoff_id}`",
        f"- **Reviewer評価勧告**: {recommendation_display}",
        f"- **最新Owner裁定**: {owner_decision_display}",
        f"- **品質目的 (Purpose)**: {purpose}",
        f"- **対象成果物**: {', '.join(f'`{t}`' for t in targets) or 'なし'}",
        f"- **Owner許可範囲**: {auth_targets} (変更許可: {'あり' if auth_allowed else 'なし'})",
    ]

    if latest_adjudication:
        decision_code = latest_adjudication.get("decision", "unknown")
        rationale = latest_adjudication.get("rationale")
        lines.extend(
            [
                "",
                "### Owner裁定の詳細",
                f"- 裁定: {owner_decision_display}",
            ]
        )
        if rationale:
            lines.append(f"- 裁定理由: {rationale}")
        if decision_code == "accepted-with-risk":
            residual_risks = latest_adjudication.get("residual_risks", [])
            conditions = latest_adjudication.get("conditions", [])
            risk_ids = [item.get("finding_id", "ID不明") for item in residual_risks if isinstance(item, dict)]
            lines.append(f"- 受容した残余リスク: {len(residual_risks)}件" + (f"（{', '.join(risk_ids)}）" if risk_ids else ""))
            lines.append("- 受入条件: " + ("、".join(str(item) for item in conditions) if conditions else "記録なし"))
            lines.append("- 残余リスクと再評価条件は保持されます。条件付き受入はリスク解消を意味しません。")
        elif decision_code == "held":
            lines.append("- 案件は停止中です。追加情報をそろえ、Owner裁定で再開を判断してください。")
        elif decision_code == "rejected":
            lines.append("- 案件はOwner裁定により却下され、終端状態です。QA GateのFAILとは別の判断です。")
        elif decision_code == "accepted":
            lines.append("- Owner受入が確定しています。この裁定は安全性の追加保証を意味しません。")

    lines.extend(["", "## 2. 不適合・課題 (Findings)"])

    all_non_proposals = [f for f in findings if f.get("classification") != "improvement-proposal"]
    if not all_non_proposals:
        lines.append("- （未解決の不適合はありません）")
    else:
        for f in all_non_proposals:
            fid = f.get("finding_id")
            cls = f.get("classification")
            sev = f.get("severity", "medium")
            fact = f.get("observed_fact", "")
            fstatus = f.get("status", "open")
            fstatus_label = FINDING_RESULT_LABELS.get(fstatus, "未定義")
            lines.append(f"- **[{fid}]** ({cls} / Severity: {sev} / 状態: {fstatus_label} (`{fstatus}`)): {fact}")

    evidence_gap_findings = [
        f for f in findings
        if f.get("status") not in RESOLVED_VERIFICATION_RESULTS
        and f.get("required_evidence")
    ]
    lines.append("")
    lines.append("## 3. 必要Evidence")
    if not evidence_gap_findings:
        lines.append("- なし")
    else:
        for f in evidence_gap_findings:
            lines.append(f"- {f.get('finding_id')}: {f.get('required_evidence')}")

    observation = case.get("change_observation", {})
    scope = observation.get("scope", []) if isinstance(observation, dict) else []
    limitations = observation.get("limitations", []) if isinstance(observation, dict) else []
    lines.append("")
    lines.append("## 4. 変更観測の範囲")
    lines.append(f"- 対象: {', '.join(str(item) for item in scope) or '未設定'}")
    if limitations:
        lines.extend(f"- {item}" for item in limitations)
    else:
        lines.append("- 観測上の制限は未登録です")

    lines.append("")
    lines.append("## 5. 改善提案（次回以降への引き継ぎ事項）")
    if not proposals:
        lines.append("- （改善提案はありません）")
    else:
        for p in proposals:
            pid = p.get("finding_id")
            fact = p.get("observed_fact", "")
            lines.append(f"- **[{pid}]**: {fact}")

    lines.append("")
    action_guide = generate_action_guide(
            case_id=case_id,
            next_role=next_role,
            next_action=next_action,
            handoff_id=handoff_id,
            traffic_color=traffic_color,
            revision=rev,
        )
    # セクション番号は必要Evidence・観測範囲の追加後も一貫させる。
    action_guide[0] = "## 6. 次の一手 (Handoff ガイド)"
    lines.extend(action_guide)

    lines.append("")
    lines.append("---")
    lines.append("*この文書は表示専用であり、案件正本ではありません。正本は `case.json` です。*")
    lines.append("")

    return "\n".join(lines)


def generate_final_risk_assessment_markdown(case: dict[str, Any]) -> str:
    meta = case.get("case_metadata", {})
    case_id = meta.get("case_id", "UNKNOWN")
    rev = meta.get("revision", meta.get("case_revision", 1))
    findings = case.get("findings", [])
    from .model import RESOLVED_VERIFICATION_RESULTS

    resolved = [f for f in findings if f.get("status") in RESOLVED_VERIFICATION_RESULTS]
    residual = [
        f
        for f in findings
        if f.get("status") not in RESOLVED_VERIFICATION_RESULTS
        and f.get("classification") != "improvement-proposal"
    ]
    crit_high = [f for f in residual if f.get("severity") in ("critical", "high")]

    assessments = case.get("final_risk_assessments", [])
    latest_assessment = assessments[-1] if assessments else None

    current_case_revision = meta.get("revision", meta.get("case_revision", 1))
    assessment_revision = (
        latest_assessment.get("revision") if latest_assessment else None
    )
    assessment_matches_current = (
        latest_assessment is not None
        and assessment_revision is not None
        and assessment_revision == current_case_revision
    )
    baseline = case.get("baseline", {})
    target_revision = baseline.get("target_revision")
    cycle_count = meta.get("cycle_count", 0)
    cycle_limit = meta.get("cycle_limit", 3)

    overall_rec = (
        latest_assessment.get("overall_recommendation") if latest_assessment else None
    )
    overall_rec_display = (
        f"{RECOMMENDATION_LABELS.get(overall_rec, '未定義')}（{overall_rec}）"
        if overall_rec
        else "未記録"
    )
    if latest_assessment and not assessment_matches_current:
        historical_revision = assessment_revision if assessment_revision is not None else "未記録"
        overall_rec_display = f"過去評価（case Revision {historical_revision}）: {overall_rec_display}"
    rationale = (
        latest_assessment.get("rationale", "")
        if latest_assessment
        else "リスク評価がまだ実施されていません。"
    )
    risk_by_id = {
        item.get("finding_id"): item
        for item in (latest_assessment or {}).get("residual_risks", [])
    }

    lines = [
        f"# 最終リスク評価報告書: {case_id} (Revision {rev})",
        "",
        "## 1. 概要指標 (Summary Metrics)",
        f"- **解決済み指摘数 (Resolved)**: {len(resolved)} 件",
        f"- **残余指摘数 (Residual)**: {len(residual)} 件",
        f"- **残余Critical/High指摘数**: {len(crit_high)} 件",
        f"- **Final Risk coverage**: {len(risk_by_id)}/{len(residual)} 件",
        f"- **Reviewer評価勧告**: {overall_rec_display}",
        (
            f"- **評価結果の対象版・サイクル**: `{target_revision}` / {cycle_count}/{cycle_limit} "
            f"（評価記録と現在のcase Revision {current_case_revision}が一致）"
            if assessment_matches_current and target_revision
            else (
                f"- **評価結果の対象版・サイクル**: 未特定（baseline.target_revisionが未記録） / "
                f"{cycle_count}/{cycle_limit}（評価記録と現在のcase Revision {current_case_revision}が一致）"
                if assessment_matches_current
                else (
                    f"- **評価結果の対象版・サイクル**: 過去評価の対象は特定不能 "
                    f"（評価記録 Revision {assessment_revision if assessment_revision is not None else '未記録'}に未記録）"
                    if latest_assessment
                    else "- **評価結果の対象版・サイクル**: 評価結果は未記録"
                )
            )
        ),
        (
            f"- **現在の対象に対する評価**: 未記録（case Revision {current_case_revision}、"
            f"対象版 `{target_revision or '未特定'}`、サイクル {cycle_count}/{cycle_limit}）"
            if latest_assessment and not assessment_matches_current
            else ""
        ),
        "",
        "## 2. QA評価所見 (QA Rationale)",
        f"> {rationale}",
        "",
        "## 3. 残余リスク評価詳細 (Residual Risks & Mitigation Details)",
    ]

    if latest_assessment:
        for f in residual:
            fid = f.get("finding_id")
            r = risk_by_id.get(fid)
            if r is None:
                status_code = f.get("status", "open")
                lines.append(f"### 指摘 [{fid}] (状態: {FINDING_RESULT_LABELS.get(status_code, '未定義')} (`{status_code}`))")
                lines.append("- **残余リスク評価**: 未提出（Core coverage違反）")
                lines.append("")
                continue
            status = f.get("status", "open")
            desc = r.get("residual_risk_description")
            like = r.get("likelihood")
            imp = r.get("impact")
            qa_rec = r.get("qa_recommendation")
            conf = r.get("confidence")
            prop = r.get("proportionality_assessment", "")
            controls = r.get("implemented_controls", [])
            assumptions = r.get("assumptions_supporting_acceptance", [])
            alternatives = r.get("alternatives", [])
            triggers = r.get("reassessment_triggers", [])

            status_label = FINDING_RESULT_LABELS.get(status, "未定義")
            lines.append(f"### 指摘 [{fid}] (状態: {status_label} (`{status}`) / Severity: `{f.get('severity')}`)")
            lines.append(f"- **残余リスク説明**: {desc}")
            lines.append(f"- **リスク評価**: 発生可能性: `{like}` / 影響度: `{imp}` / 確信度: `{conf}`")
            qa_rec_label = RECOMMENDATION_LABELS.get(qa_rec, "未定義")
            lines.append(f"- **Reviewer個別勧告**: {qa_rec_label}（{qa_rec}）")
            if controls:
                lines.append(f"- **実装済み対策 (Implemented Controls)**: {', '.join(controls)}")
            if assumptions:
                lines.append(f"- **受入前提条件 (Acceptance Assumptions)**: {', '.join(assumptions)}")
            if alternatives:
                lines.append(f"- **代替策・選択肢 (Alternatives)**: {', '.join(alternatives)}")
            if prop:
                lines.append(f"- **比例性・妥当性評価 (Proportionality)**: {prop}")
            if triggers:
                lines.append(f"- **再評価トリガー (Reassessment Triggers)**: {', '.join(triggers)}")
            lines.append("")
    elif not residual:
        lines.append("- （残余リスクはありません。全件解決済みです）\n")
    else:
        for f in residual:
            lines.append(f"- **[{f.get('finding_id')}]** ({f.get('classification')} / Severity: {f.get('severity')}): {f.get('observed_fact')}")
        lines.append("")

    lines.append("## 4. Owner意思決定オプション (Decision Options)")
    lines.append("1. **受入 (accepted)**: 未解決の対象Findingがなく、独立検証結果と基準を確認したOwnerが受入を確定します。安全性の追加保証を意味しません。")
    lines.append("2. **残余リスク付き受入 (accepted-with-risk)**: 記録された残余リスクと補償条件を確認したOwnerが明示的に受容します。リスクは解消扱いにならず、再評価条件を保持します。")
    lines.append("3. **再作業指示 (rework-requested)**: 対象Findingと許可範囲を指定し、必要な追加サイクルを付与して再作業を依頼します。実装許可はこの記録の範囲に限られます。")
    lines.append("4. **保留 (held)**: 案件を停止し、不足情報・理由・再開条件を確認後にOwner裁定を再開します。終端判断ではありません。")
    lines.append("5. **却下 (rejected)**: Ownerが案件を却下して終端とします。これはQA GateのFAILとは別の判断です。")
    lines.append("")
    lines.append("---")
    lines.append("*この文書は表示専用サマリーです。案件正本は `case.json` です。*")
    lines.append("")

    return "\n".join(lines)
