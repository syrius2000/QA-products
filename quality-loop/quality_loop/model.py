from __future__ import annotations

from .errors import QualityLoopError


FINDING_REQUIRED_FIELDS = (
    "finding_id",
    "classification",
    "severity",
    "requirement_ref",
    "observed_fact",
    "impact",
    "expected_state",
    "verification_method",
    "evidence_refs",
)

FINDING_CLASSIFICATIONS = {
    "requirement-violation",
    "purpose-risk",
    "evidence-gap",
    "improvement-proposal",
}

SEVERITIES = {"critical", "high", "medium", "low"}


def validate_findings(findings: object, existing_ids: set[str]) -> list[dict]:
    if not isinstance(findings, list):
        raise QualityLoopError(
            "invalid-input",
            "findingsは配列で指定してください。",
            remediation="Finding配列または空配列を指定してください。",
        )
    validated: list[dict] = []
    observed_ids = set(existing_ids)
    for finding in findings:
        if not isinstance(finding, dict):
            raise QualityLoopError("invalid-finding", "Findingはobjectで指定してください。")
        missing = [field for field in FINDING_REQUIRED_FIELDS if field not in finding]
        if missing:
            raise QualityLoopError(
                "invalid-finding",
                f"Finding必須項目が不足しています: {', '.join(missing)}",
                remediation="要求、事実、影響、期待状態、検証方法、Evidence参照を補完してください。",
            )
        finding_id = finding["finding_id"]
        if finding_id in observed_ids:
            raise QualityLoopError(
                "duplicate-finding-id",
                f"Finding ID {finding_id} は既に存在します。",
            )
        if finding["classification"] not in FINDING_CLASSIFICATIONS:
            raise QualityLoopError("invalid-finding", "未対応のFinding分類です。")
        if finding["severity"] not in SEVERITIES:
            raise QualityLoopError("invalid-finding", "未対応のSeverityです。")
        evidence_refs = finding["evidence_refs"]
        if not isinstance(evidence_refs, list) or not all(
            isinstance(item, str) and item for item in evidence_refs
        ):
            raise QualityLoopError(
                "invalid-finding",
                "Findingのevidence_refsは空でないEvidence ID配列で指定してください。",
            )
        if not evidence_refs:
            if not finding.get("unverified_reason") or not finding.get("required_evidence"):
                raise QualityLoopError(
                    "finding-evidence-required",
                    "FindingにはEvidence参照が必要です。Evidence不足の場合はunverified_reasonとrequired_evidenceを指定してください。",
                )
        observed_ids.add(finding_id)
        validated.append(finding)
    return validated
