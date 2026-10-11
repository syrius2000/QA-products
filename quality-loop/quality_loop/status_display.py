"""正式案件statusの読み取り専用な人向け表示。"""
from __future__ import annotations

from typing import Any


CASE_STATUS_STAGES = {
    "reviewer-action": ("QA・確認", "Reviewerのレビューまたは再レビュー待ち"),
    "reviewer-plan-review": ("QA・確認", "修正計画のReviewer審査待ち"),
    "reviewer-verification": ("QA・確認", "提出修正の独立検証待ち"),
    "reviewer-final-assessment": ("QA・確認", "残余リスクの最終評価待ち"),
    "implementer-plan": ("修正", "修正計画の提出待ち。計画承認前の実装は許可されていない"),
    "implementer-action": ("修正", "許可範囲内の回答・修正提出待ち"),
    "owner-adjudication": ("判断待ち", "Reviewer結果と残余事項に対するOwner裁定待ち"),
    "held": ("判断待ち", "停止中。Owner裁定による再開判断待ち"),
    "accepted": ("終了", "Ownerが受入を確定"),
    "accepted-with-risk": ("終了", "Ownerが残余リスク付き受入を確定"),
    "rejected": ("終了", "Ownerが案件を却下"),
}

ROLE_LABELS = {
    "reviewer": "レビュー担当",
    "implementer": "実装担当",
    "owner": "Owner",
}

ACTION_LABELS = {
    "review": "レビュー",
    "submit-plan": "修正計画の提出",
    "review-plan": "修正計画の審査",
    "submit-response": "Finding別回答の提出",
    "verify": "修正内容の独立検証",
    "assess-risk": "残余リスクの最終評価",
    "adjudicate": "Owner裁定",
}

FINDING_RESULT_LABELS = {
    "open": "未対応",
    "verified": "検証済み",
    "not-verified": "未確認",
    "unverified": "未検証",
    "remediated": "修正済み",
    "not-remediated": "未修正",
    "partially-remediated": "一部修正",
    "finding-withdrawn": "指摘撤回",
    "converted-to-suggestion": "改善提案へ変更",
    "not-applicable": "非該当",
    "requires-rereview": "再レビュー要",
    "held": "保留",
}

RECOMMENDATION_LABELS = {
    "accept": "受入推奨",
    "accept-with-conditions": "条件付き受入推奨",
    "require-remediation": "修正要求推奨",
    "defer": "判断延期推奨",
}


def risk_recommendation_display(case: dict[str, Any], *, lang: str = "ja") -> str:
    """勧告記録のcase Revisionを照合し、過去結果を現在版へ適用しない。"""
    assessments = case.get("final_risk_assessments", [])
    if not assessments:
        return "未記録" if lang == "ja" else "not recorded"
    record = assessments[-1]
    code = record.get("overall_recommendation", "unknown")
    value = f"{RECOMMENDATION_LABELS.get(code, '未定義')}（{code}）" if lang == "ja" else code
    metadata = case.get("case_metadata", {})
    current_revision = metadata.get("revision", metadata.get("case_revision"))
    record_revision = record.get("revision")
    if record_revision is not None and record_revision == current_revision:
        target = case.get("baseline", {}).get("target_revision")
        cycle = metadata.get("cycle_count")
        if lang == "ja":
            return f"{value} ／ 対象版 {target or '未特定'} ／ サイクル {cycle if cycle is not None else '未特定'} ／ case Revision {record_revision}"
        return f"{value} / target {target or 'unknown'} / cycle {cycle if cycle is not None else 'unknown'} / case Revision {record_revision}"
    # 旧記録には評価時の対象版・cycleのsnapshotがないため、現在値を補記しない。
    if lang == "ja":
        return f"未記録（現在版）。過去評価（case Revision {record_revision if record_revision is not None else '未記録'}、対象版・サイクル未特定）: {value}"
    return f"not recorded for current revision; historical assessment (case Revision {record_revision if record_revision is not None else 'unknown'}, target and cycle unknown): {value}"


def stage_for_case_status(status: dict[str, Any]) -> tuple[str, str]:
    """正式案件の既知状態を5工程へ対応させ、未知値は未定義にする。"""
    state = status.get("current_state")
    known = CASE_STATUS_STAGES.get(state)
    if known:
        stage, detail = known
        if state == "held":
            handoff = status.get("handoff") or {}
            reason = handoff.get("purpose")
            if reason:
                detail = f"停止中（Owner裁定待ち）: {reason}"
        return stage, detail
    return "未定義", f"未定義の正式案件状態: {state!r}。状態・Role・操作を確認してください"


def _recorded_verifications(case: dict[str, Any]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(case.get("verifications", [])):
        finding_id = item.get("finding_id")
        if not finding_id:
            continue
        previous = latest.get(finding_id)
        revision = item.get("verification_revision", index)
        previous_revision = previous.get("verification_revision", -1) if previous else -1
        if previous is None or revision >= previous_revision:
            latest[finding_id] = item
    return [latest[key] for key in sorted(latest)]


def render_case_status(
    status: dict[str, Any], *, case: dict[str, Any] | None = None, lang: str = "ja"
) -> str:
    """status要約と案件記録から表示を作る。入力の変更・保存はしない。"""
    if lang not in {"ja", "en"}:
        raise ValueError("langはjaまたはenを指定してください")
    state = status.get("current_state", "unknown")
    stage, detail = stage_for_case_status(status)
    handoff = status.get("handoff") or {}
    next_role = handoff.get("next_role")
    next_action = handoff.get("next_action")
    owner_role_required = status.get("owner_decisions_required")

    if lang == "en":
        lines = [
            f"Case {status.get('case_id', 'unknown')} / revision {status.get('case_revision', 'unknown')} / state {state}",
            f"Stage: {stage}",
            f"Details: {detail}",
        ]
        lines.append(f"Next role: {next_role or 'none'}")
        lines.append(f"Next action: {next_action or 'none'}")
    else:
        lines = [
            f"正式案件 {status.get('case_id', '不明')} ／ revision {status.get('case_revision', '不明')} ／ 状態 {state}",
            f"工程: {stage}",
            f"詳細: {detail}",
        ]
        if next_role:
            lines.append(f"次の担当: {ROLE_LABELS.get(next_role, '未定義')}（{next_role}）")
        else:
            lines.append("次の担当: なし（終端）")
        if next_action:
            lines.append(f"次の操作: {ACTION_LABELS.get(next_action, '未定義')}（{next_action}）")
        else:
            lines.append("次の操作: なし（終端）")

    if owner_role_required:
        lines.append("停止・判断待ち: Ownerの裁定が必要です" if lang == "ja" else "Stop / decision pending: Owner adjudication is required")

    purpose = handoff.get("purpose")
    if purpose and state in {"owner-adjudication", "held"}:
        lines.append(f"判断の理由: {purpose}" if lang == "ja" else f"Decision context: {purpose}")

    open_findings = status.get("open_findings", [])
    gaps = status.get("evidence_gaps", [])
    if lang == "ja":
        lines.append(f"未解決Finding: {len(open_findings)}件" + (f"（{', '.join(open_findings)}）" if open_findings else ""))
        lines.append(f"Evidence不足: {len(gaps)}件" + (f"（{', '.join(gaps)}）" if gaps else ""))
    else:
        lines.append(f"Open findings: {len(open_findings)}" + (f" ({', '.join(open_findings)})" if open_findings else ""))
        lines.append(f"Evidence gaps: {len(gaps)}" + (f" ({', '.join(gaps)})" if gaps else ""))

    if case:
        metadata = case.get("case_metadata", {})
        baseline = case.get("baseline", {})
        target_revision = baseline.get("target_revision")
        if lang == "ja":
            lines.append(
                f"評価対象版（baseline.target_revision）: {target_revision or '未特定'}"
            )
        else:
            lines.append(
                f"Evaluation target revision (baseline.target_revision): {target_revision or 'unknown'}"
            )
        cycle_count = metadata.get("cycle_count")
        cycle_limit = metadata.get("cycle_limit")
        if cycle_count is not None:
            if lang == "ja":
                lines.append(f"サイクル: {cycle_count}/{cycle_limit if cycle_limit is not None else '不明'}")
            else:
                lines.append(f"Cycle: {cycle_count}/{cycle_limit if cycle_limit is not None else 'unknown'}")
        authorization = status.get("implementation_authorization") or case.get("implementation_authorization", {})
        if lang == "ja":
            allowed = "あり" if authorization.get("allowed") else "なし"
            targets = ", ".join(authorization.get("allowed_targets", [])) or "なし"
            lines.append(f"実装許可: {allowed} ／ 許可対象: {targets}")
        else:
            allowed = "yes" if authorization.get("allowed") else "no"
            targets = ", ".join(authorization.get("allowed_targets", [])) or "none"
            lines.append(f"Implementation authorization: {allowed} / allowed targets: {targets}")
        for item in _recorded_verifications(case):
            finding_id = item["finding_id"]
            result = item.get("result", "unknown")
            label = FINDING_RESULT_LABELS.get(result, "未定義")
            revision = item.get("verification_revision", "不明")
            if lang == "ja":
                lines.append(f"検証結果: {finding_id}＝{label}（{result}、revision {revision}）")
            else:
                lines.append(f"Verification: {finding_id}={result} (revision {revision})")
        recommendation = risk_recommendation_display(case, lang=lang)
        lines.append(f"Reviewer評価勧告: {recommendation}" if lang == "ja" else f"Reviewer recommendation: {recommendation}")
        if state == "held" and case.get("adjudications"):
            latest_decision = case["adjudications"][-1]
            if latest_decision.get("decision") == "held" and latest_decision.get("rationale"):
                lines.append(f"保留理由: {latest_decision['rationale']}" if lang == "ja" else f"Hold rationale: {latest_decision['rationale']}")

    if case is not None and any(item.get("status") not in FINDING_RESULT_LABELS for item in case.get("findings", [])):
        lines.append("未定義のFinding状態があります。原記録を確認してください" if lang == "ja" else "An unknown finding status is present; inspect the source record")
    return "\n".join(lines)
