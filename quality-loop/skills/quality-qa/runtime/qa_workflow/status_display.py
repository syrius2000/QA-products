"""人向けQA状態表示の読み取り専用な工程対応。"""
from __future__ import annotations

from typing import Any


QA_GATE_LABELS = {
    "PASS": "基準充足",
    "FAIL": "基準未達",
    "HOLD": "保留",
    "INCONCLUSIVE": "判定不能",
}


PHASE_STAGES = {
    "draft": ("準備", "QA対象の確定待ち"),
    "prepared": ("準備", "QA依頼を準備済み"),
    "published": ("QA・確認", "公開済みのQA依頼をレビュー待ち"),
    "waiting": ("QA・確認", "レビュー結果待ち"),
    "content_pending": ("QA・確認", "取得したレビュー内容の妥当性を確認待ち"),
    "invalid": ("QA・確認", "レビュー結果の不備または訂正待ち"),
    "planned": ("判断待ち", "修正計画の承認待ち"),
    "approved": ("修正", "承認済み範囲の修正と提出待ち"),
    "submitted": ("QA・確認", "修正提出済み、独立再QA待ち"),
    "decision": ("終了", "利用者の終了判断を記録済み"),
}


def stage_for_status(status: dict[str, Any], *, pending_correction: bool = False) -> tuple[str, str]:
    """状態と既存の次操作案内から基本工程と詳細を返す。"""
    phase = status.get("phase")
    next_step = status.get("next") or {}
    reason = str(next_step.get("理由") or "")

    # 公開拒否はphaseを書き換えず、一般的な依頼状態より先に扱う。
    if "最終公開走査で拒否" in reason:
        return "判断待ち", "停止: 公開走査で拒否。原因を除いた新しいQA依頼が必要"

    if pending_correction or phase == "invalid" or "不備または訂正待ち" in reason:
        return "QA・確認", "停止: レビュー結果の不備または訂正待ち。記録された次の操作と必要入力を確認してください"

    if phase == "reviewed":
        if "重大問題" in reason or "要求未達" in reason:
            return "修正", "未達事項への修正計画が必要"
        if "未完了" in reason or "PASS以外" in reason:
            return "QA・確認", "必須確認または判定内容の確認が必要"
        if "終了判断" in reason or "終了判断" in str(next_step.get("操作") or ""):
            return "判断待ち", "利用者の終了判断待ち"
        return "未定義", f"未定義の状態: {phase}（次工程を特定できません）"

    if phase in PHASE_STAGES:
        return PHASE_STAGES[phase]
    return "未定義", f"未定義の状態: {phase!r}。担当者による確認が必要"


def assessment_from_state(state: dict[str, Any]) -> dict[str, Any] | None:
    """有効化済みのQA判定を、保存値のまま対象版・サイクルへ結び付ける。"""
    if state.get("phase") not in {"reviewed", "planned", "approved", "submitted", "decision"} or state.get("pending_correction"):
        return None
    active_hash = state.get("active_review")
    if not active_hash:
        return None
    review = next(
        (
            item
            for item in state.get("reviews", [])
            if item.get("hash") == active_hash
            and item.get("content_checked")
            and not item.get("issues")
        ),
        None,
    )
    if not review:
        return None
    parsed = review.get("parsed")
    gate = parsed.get("gate") if isinstance(parsed, dict) else None
    if gate not in QA_GATE_LABELS:
        return None
    return {
        "request_id": state.get("id"),
        "target_sha": state.get("reviewed"),
        "cycle": state.get("cycle"),
        "gate": gate,
    }


def resolve_assessments(
    state: dict[str, Any], load_previous: Any
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """現在結果と直近の記録済み過去結果を、依頼のprevious鎖から取得する。"""
    current = assessment_from_state(state)
    previous = None
    request_id = state.get("previous")
    seen = {state.get("id")}
    while request_id and request_id not in seen:
        seen.add(request_id)
        older = load_previous(request_id)
        previous = assessment_from_state(older)
        if previous:
            break
        request_id = older.get("previous")
    return current, previous


def _assessment_line(
    assessment: dict[str, Any], *, lang: str, historical: bool = False
) -> str:
    gate = assessment["gate"]
    target = assessment.get("target_sha") or ("不明" if lang == "ja" else "unknown")
    cycle = assessment.get("cycle") or ("不明" if lang == "ja" else "unknown")
    request_id = assessment.get("request_id")
    if lang == "en":
        prefix = "Previous QA result" if historical else "Current-cycle QA result"
        request = f" / request {request_id}" if request_id else ""
        return f"{prefix}: Gate {gate} / target SHA {target} / cycle {cycle}{request}"
    label = QA_GATE_LABELS[gate]
    prefix = "過去のQA判定" if historical else "現在サイクルのQA判定"
    request = f" ／ 依頼 {request_id}" if request_id else ""
    return f"{prefix}: {label}（{gate}）／対象版 {target}／サイクル {cycle}{request}"


def render_status(
    status: dict[str, Any],
    *,
    lang: str = "ja",
    current_assessment: dict[str, Any] | None = None,
    previous_assessment: dict[str, Any] | None = None,
    pending_correction: bool = False,
) -> str:
    """通常QAの状態を人向けに描画する。JSON状態を変更しない。"""
    if lang not in {"ja", "en"}:
        raise ValueError("langはjaまたはenを指定してください")

    if lang == "en":
        # 英語選択は既存コードと表示語彙の互換表示とする。
        phase = status.get("phase", "unknown")
        next_step = status.get("next") or {}
        lines = [
            f"依頼 {status.get('id', '不明')} ／ サイクル {status.get('cycle', '不明')} ／ 状況 {phase}",
            f"Target SHA: {status.get('reviewed') or 'unknown'}",
        ]
        if current_assessment:
            lines.append(_assessment_line(current_assessment, lang=lang))
        else:
            lines.append("Current-cycle QA result: none (not recorded)")
        if previous_assessment:
            lines.append(_assessment_line(previous_assessment, lang=lang, historical=True))
        for key in ("担当", "操作", "理由", "必要入力"):
            if next_step.get(key):
                lines.append(f"{key}: {next_step[key]}")
        lines.extend(_status_details(status))
        return "\n".join(lines)

    if status.get("error"):
        lines = [f"確認待ち: {status['error']}"]
        next_step = status.get("next") or {}
        for key in ("担当", "操作", "理由", "必要入力"):
            if next_step.get(key):
                lines.append(f"{key}: {next_step[key]}")
        lines.extend(_status_details(status))
        return "\n".join(lines)

    stage, detail = stage_for_status(status, pending_correction=pending_correction)
    lines = [
        f"QA依頼 {status.get('id', '不明')} ／ サイクル {status.get('cycle', '不明')} ／ 工程 {stage}",
        f"詳細: {detail}",
        f"評価対象版: {status.get('reviewed') or '未確定'}",
    ]
    if current_assessment:
        lines.append(_assessment_line(current_assessment, lang=lang))
    else:
        lines.append("現在サイクルのQA判定: なし（未記録）")
    if previous_assessment:
        lines.append(_assessment_line(previous_assessment, lang=lang, historical=True))
    next_step = status.get("next") or {}
    for key in ("担当", "操作", "理由", "必要入力"):
        value = next_step.get(key)
        if value:
            lines.append(f"{key}: {value}")
    lines.extend(_status_details(status))
    return "\n".join(lines)


def _status_details(status: dict[str, Any]) -> list[str]:
    """既存の人向け案内本文とレビュー不備一覧を省略せず表示する。"""
    lines = []
    invitation = (status.get("next") or {}).get("依頼文")
    if invitation:
        lines.append("\n渡す文書:\n" + invitation)
    lines.extend("確認事項: " + issue for issue in status.get("issues", []))
    return lines


def render_preflight(result: dict[str, Any], *, lang: str = "ja") -> str:
    """Git事前確認を選択言語で表示する。"""
    if lang not in {"ja", "en"}:
        raise ValueError("langはjaまたはenを指定してください")
    if lang == "en":
        lines = [
            f"Git preflight: {'clean' if result['clean'] else 'dirty'} ／ 実装可能: {'はい' if result['safe_to_implement'] else 'いいえ'}",
            f"repo: {result['repository_root']}",
            f"branch: {result['branch'] or '不明'}",
            f"HEAD: {result['head'] or '不明'}",
            f"upstream: {result['upstream'] or '不明'}",
            f"既定branch: {result['default_branch'] or '不明'}",
        ]
        for key in ("staged", "unstaged", "untracked"):
            lines.append(f"{key}: {', '.join(result[key]) if result[key] else 'なし'}")
    else:
        lines = [
            f"Git事前確認: {'変更なし' if result['clean'] else '変更あり'} ／ 実装開始可能: {'はい' if result['safe_to_implement'] else 'いいえ'}",
            f"リポジトリ: {result['repository_root']}",
            f"ブランチ: {result['branch'] or '不明'}",
            f"HEAD: {result['head'] or '不明'}",
            f"追跡先: {result['upstream'] or '不明'}",
            f"既定ブランチ: {result['default_branch'] or '不明'}",
            f"ステージ済み: {', '.join(result['staged']) if result['staged'] else 'なし'}",
            f"未ステージ: {', '.join(result['unstaged']) if result['unstaged'] else 'なし'}",
            f"未追跡: {', '.join(result['untracked']) if result['untracked'] else 'なし'}",
        ]
    lines.append(str(result["next"]))
    return "\n".join(lines)
