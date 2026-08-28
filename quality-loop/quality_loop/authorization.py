from __future__ import annotations

from .errors import QualityLoopError


def validate_authorization(authorization: object) -> dict:
    if not isinstance(authorization, dict):
        raise QualityLoopError(
            "invalid-authorization",
            "implementation_authorizationはobjectで指定してください。",
        )
    required = ("allowed", "finding_ids", "allowed_targets")
    missing = [field for field in required if field not in authorization]
    if missing:
        raise QualityLoopError(
            "invalid-authorization",
            f"実装許可の必須項目が不足しています: {', '.join(missing)}",
        )
    if not isinstance(authorization["allowed"], bool):
        raise QualityLoopError("invalid-authorization", "allowedはbooleanで指定してください。")
    for field in ("finding_ids", "allowed_targets"):
        values = authorization[field]
        if not isinstance(values, list) or any(
            not isinstance(item, str) or not item for item in values
        ):
            raise QualityLoopError(
                "invalid-authorization",
                f"{field}は空文字を含まない文字列配列で指定してください。",
            )
    if not authorization["allowed"] and (
        authorization["finding_ids"] or authorization["allowed_targets"]
    ):
        raise QualityLoopError(
            "invalid-authorization",
            "allowedがfalseの場合は許可対象を空にしてください。",
        )
    return {
        "allowed": authorization["allowed"],
        "finding_ids": list(dict.fromkeys(authorization["finding_ids"])),
        "allowed_targets": list(dict.fromkeys(authorization["allowed_targets"])),
    }


def validate_changed_targets(
    authorization: dict,
    *,
    finding_ids: set[str],
    changed_targets: object,
) -> list[str]:
    if not isinstance(changed_targets, list) or any(
        not isinstance(item, str) or not item for item in changed_targets
    ):
        raise QualityLoopError(
            "invalid-input",
            "changed_targetsは空文字を含まない文字列配列で指定してください。",
        )
    unique_targets = list(dict.fromkeys(changed_targets))
    if not unique_targets:
        return unique_targets
    if not authorization.get("allowed", False):
        raise QualityLoopError(
            "implementation-not-authorized",
            "Ownerによる実装許可がありません。",
            remediation="Ownerへ実装範囲の裁定を依頼してください。",
        )
    allowed_targets = set(authorization.get("allowed_targets", []))
    unauthorized_targets = sorted(set(unique_targets) - allowed_targets)
    if unauthorized_targets:
        raise QualityLoopError(
            "unauthorized-change-detected",
            f"許可外の変更対象です: {', '.join(unauthorized_targets)}",
            remediation="変更を戻すか、Ownerへ許可範囲の裁定を依頼してください。",
        )
    authorized_findings = set(authorization.get("finding_ids", []))
    if authorized_findings and not finding_ids.issubset(authorized_findings):
        unauthorized_findings = sorted(finding_ids - authorized_findings)
        raise QualityLoopError(
            "implementation-not-authorized",
            f"実装許可のないFindingです: {', '.join(unauthorized_findings)}",
        )
    return unique_targets
