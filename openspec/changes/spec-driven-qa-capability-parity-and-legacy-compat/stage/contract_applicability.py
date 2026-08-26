#!/usr/bin/env python3
"""三版で異なる安全・digest契約の適用可能性を合格と混同せず記録するCLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def item(version: str, control: str, status: str, evidence: str, detail: str) -> dict[str, str]:
    return {
        "version": version,
        "control": control,
        "status": status,
        "evidence": evidence,
        "detail": detail,
    }


def build_report(stage: Path) -> dict[str, Any]:
    safety = json.loads((stage / "evidence" / "safety-regression.json").read_text(encoding="utf-8"))
    candidate_probe = json.loads((stage / "evidence" / "candidate-contract-probe.json").read_text(encoding="utf-8"))
    candidate_digest_probe = json.loads((stage / "evidence" / "candidate-digest-probe.json").read_text(encoding="utf-8"))
    checks = {
        version: {check["id"]: check["status"] for check in data["checks"]}
        for version, data in safety["bundles"].items()
    }
    def observed(checks_for_version: dict[str, str], check_id: str) -> str:
        return "observed" if checks_for_version.get(check_id) == "passed" else "evidence-gap"

    rows = [
        item("legacy", "author-self-close", "not-applicable", "cross-skill/codex-20260827-compat-01/manifest.json", "後発の状態Firewall契約がLegacyにない"),
        item("candidate", "author-self-close-and-reviewer-write", observed(checks["candidate"], "candidate-author-reviewer-field-denied"), "safety-regression.json", "CandidateのReviewer所有フィールド拒否を確認"),
        item("compact", "author-self-close-and-reviewer-write", observed(checks["compact"], "compact-author-self-close-denied"), "safety-regression.json", "compactのAuthor役割境界とReviewer所有フィールド拒否を確認"),
        item("legacy", "unknown-finding", "not-applicable", "cross-skill/codex-20260827-compat-01/manifest.json", "Legacyに後発Finding validator契約がない"),
        item("candidate", "unknown-finding", observed(checks["candidate"], "candidate-unknown-finding-denied"), "safety-regression.json", "Candidateの未知Finding拒否を確認"),
        item("compact", "unknown-finding", observed(checks["compact"], "compact-unknown-finding-denied"), "safety-regression.json", "compactの未知Finding拒否を確認"),
        item("legacy", "empty-or-missing-evidence", "not-applicable", "compatibility-report.json", "LegacyにEvidence validator契約がない"),
        item("candidate", "empty-or-missing-evidence", "failed" if candidate_probe.get("status") == "observed-violation" else "evidence-gap", "candidate-contract-probe.json", "Candidateは空Evidenceを受理したため、期待rejectに対する観測違反として記録"),
        item("compact", "empty-or-missing-evidence", "not-applicable", "spec-driven-qa-bundle/shared_core/chain.py", "compact連鎖APIはEvidence bundle契約を定義していない"),
        item("legacy", "workspace-outside-path", "not-applicable", "compatibility-report.json", "Legacyに共通Workspace境界契約がない"),
        item("candidate", "workspace-outside-path", observed(checks["candidate"], "candidate-workspace-absolute-repository-path-denied"), "safety-regression.json", "Candidateのrepository-relative参照拒否を確認"),
        item("compact", "workspace-outside-path", observed(checks["compact"], "compact-workspace-boundary-denied"), "safety-regression.json", "compactのWorkspace外パス拒否を確認"),
        item("legacy", "digest-contract", "not-applicable", "cross-skill/codex-20260827-compat-01/manifest.json", "Legacyにsemantic/content digest契約がない"),
        item("candidate", "stale-semantic-digest", candidate_digest_probe.get("status", "evidence-gap"), "candidate-digest-probe.json", "Candidateに実在するsemantic digestのstale拒否を実測"),
        item("candidate", "content-digest-and-version", "not-applicable", "compatibility-report.json", "Candidateの現行Bundleに分離content digest/version契約がない"),
        item("compact", "stale-semantic-and-content-digest", "observed", "safety-regression.json", "compactのstale semantic/content digest拒否を確認"),
        item("compact", "unknown-digest-version", observed(checks["compact"], "compact-unknown-digest-version-denied"), "safety-regression.json", "compactの未知digest version拒否を確認"),
        item("compact", "legacy-equivalent-digest", "observed", "docs/ADR/QA/QA-0007-separate-semantic-content-digests/review.md", "QA-0007の旧同値digest拒否プローブを参照"),
    ]
    blocking = [row for row in rows if row["status"] in {"evidence-gap", "unverified", "failed"}]
    return {
        "schema_version": "contract-applicability-1",
        "status": "evidence-gap" if blocking else "observed",
        "policy": "not-applicableとevidence-gapは合格とみなさず、Legacyの後発契約不在は意図的非互換として分離する",
        "rows": rows,
        "blocking_rows": len(blocking),
        "pass_eligible": not blocking,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_report(args.stage.resolve())
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": report["status"], "blocking_rows": report["blocking_rows"]}, ensure_ascii=False))
    return 0 if report["status"] == "observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
