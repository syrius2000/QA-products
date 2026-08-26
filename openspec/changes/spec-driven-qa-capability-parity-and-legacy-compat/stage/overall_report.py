#!/usr/bin/env python3
"""三版互換性検証の結果を人間裁定可能な形へ統合するCLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object is required: {path}")
    return value


def status_of(data: dict[str, Any], *keys: str) -> str:
    if not keys:
        keys = ("status",)
    for key in keys:
        if key in data:
            return str(data[key])
    return "evidence-gap"


def build_report(evidence_root: Path, run_id: str, adjudication_path: Path | None = None) -> dict[str, Any]:
    evidence_root = evidence_root.resolve()
    files = {
        "compatibility": evidence_root / "compatibility-report.json",
        "safety": evidence_root / "safety-regression.json",
        "contract_applicability": evidence_root / "contract-applicability.json",
        "candidate_contract_probe": evidence_root / "candidate-contract-probe.json",
        "candidate_digest_probe": evidence_root / "candidate-digest-probe.json",
        "agent_aggregate": evidence_root / "agent-aggregate.json",
        "agent_source_manifest": evidence_root / "agents" / "source-manifest.json",
        "size": evidence_root / "size-report.json",
        "runner": evidence_root / "runs" / run_id / "manifest.json",
        "cross_skill": evidence_root / "cross-skill" / run_id / "manifest.json",
    }
    missing = [name for name, path in files.items() if not path.is_file()]
    if missing:
        raise ValueError("required evidence is missing: " + ", ".join(missing))
    loaded = {name: read_json(path) for name, path in files.items()}
    adjudication: dict[str, Any] = {}
    if adjudication_path is not None:
        adjudication = read_json(adjudication_path.resolve())
        if adjudication.get("case_id") != "QA-0008":
            raise ValueError("human adjudication case_id must be QA-0008")
        if adjudication.get("decision") not in {"accepted-with-residual-risk", "conditionally-accepted", "hold"}:
            raise ValueError("unsupported human adjudication decision")
    statuses = {
        "compatibility": status_of(loaded["compatibility"], "overall_status", "status"),
        "safety": status_of(loaded["safety"]),
        "contract_applicability": status_of(loaded["contract_applicability"]),
        "candidate_contract_probe": status_of(loaded["candidate_contract_probe"]),
        "candidate_digest_probe": status_of(loaded["candidate_digest_probe"]),
        "agent_aggregate": status_of(loaded["agent_aggregate"]),
        "agent_source_manifest": status_of(loaded["agent_source_manifest"]),
        "size": status_of(loaded["size"]),
        "runner": "observed" if loaded["runner"].get("run_count") == loaded["runner"].get("observed_count") else "evidence-gap",
        "cross_skill": status_of(loaded["cross_skill"], "status", "overall_status"),
    }
    statuses["human_adjudication"] = "observed" if adjudication else "unverified"
    residual_risks = [
        {
            "id": "R-LEGACY-CROSS-SKILL",
            "status": "intentional-noncompatibility",
            "detail": "Legacyには後発のsubmission・digest・revision契約がなく、Candidate／compactとの連鎖完全互換を主張しない",
            "evidence": "compatibility-report.json",
        },
        {
            "id": "R-DYNAMIC-METRICS",
            "status": "unverified",
            "detail": "Agent集計ではToken・LatencyをObservedへ補完していないため、動的性能比較は未検証",
            "evidence": "agent-aggregate.json",
        },
        {
            "id": "R-CANDIDATE-CONTRACT-GAPS",
            "status": "failed",
            "detail": "Candidateの空Evidence受理という観測違反が残る。semantic digestのstale拒否はObserved、content digest／versionはCandidate契約外として分離済み",
            "evidence": "candidate-contract-probe.json, contract-applicability.json",
        },
        {
            "id": "R-AGENT-METADATA-COMPLETENESS",
            "status": "evidence-gap",
            "detail": "5 Agent／Runのうち、実行件数・Prompt suite・未実行項目などの必須メタデータを全項目確認できるRunは一部に限られる",
            "evidence": "agent-aggregate.json",
        },
        {
            "id": "R-NO-DEPLOYMENT",
            "status": "not-performed",
            "detail": "外部Skill配置、Legacy削除、commit、pushは本Changeの範囲外で未実施",
            "evidence": "overall-report.json",
        },
    ]
    overall_status = "observed" if all(value == "observed" for value in statuses.values()) else "evidence-gap"
    decision = adjudication.get("decision", "human-adjudication-required")
    evidence_files = {name: str(path.relative_to(evidence_root)) for name, path in files.items()}
    if adjudication_path is not None:
        evidence_files["human_adjudication"] = str(adjudication_path.resolve().relative_to(evidence_root))
    return {
        "schema_version": "overall-parity-report-1",
        "status": overall_status,
        "decision": decision,
        "decision_policy": "evidence-gap、unverified、intentional-noncompatibilityを合格へ集約せず、compact採用可否は人間裁定とする",
        "run_id": run_id,
        "gate_status": {
            "G0_bundle_and_fixture_boundary": statuses["runner"],
        "G1_compatibility_and_safety": "observed" if all(statuses[key] == "observed" for key in ("safety", "contract_applicability", "compatibility")) else "evidence-gap",
        "G2_external_agent_evidence": "observed-with-unverified" if statuses["agent_aggregate"] == "observed-with-unverified" and statuses["agent_source_manifest"] == "observed" else "evidence-gap",
        "G3_human_adjudication": statuses["human_adjudication"],
        },
        "input_statuses": statuses,
        "residual_risks": residual_risks,
        "evidence_files": evidence_files,
        "adjudication": adjudication or {"status": "pending"},
        "promotion": {"allowed": False, "reason": "条件付き受入後も、外部配備は別Changeと明示承認が必要" if adjudication else "独立QAと人間裁定、および外部配備計画が未完了"},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, default=Path(__file__).resolve().parent / "evidence")
    parser.add_argument("--run-id", default="codex-20260827-compat-01")
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_report(args.evidence_root.resolve(), args.run_id, args.adjudication)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": report["status"], "decision": report["decision"]}, ensure_ascii=False))
    return 0 if report["status"] == "observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
