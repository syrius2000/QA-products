#!/usr/bin/env python3
"""三版Evidenceを機能単位の互換性差分へ分類する標準ライブラリCLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CLASSIFICATIONS = {
    "compatible",
    "intentional-noncompatibility",
    "presentation-only",
    "missing-or-unverified",
}
ROLE_ROOTS = {
    "legacy": {"reviewer": "spec-driven-qa-review", "author": "spec-driven-qa-author-response"},
    "candidate": {"reviewer": "spec_driven_qa_reviewer", "author": "spec_driven_qa_author_response"},
    "compact": {"reviewer": "spec-driven-qa-review", "author": "spec-driven-qa-author-response"},
}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object is required: {path}")
    return value


def bundle_file_sets(bundle_manifest: dict[str, Any]) -> dict[str, set[str]]:
    bundles: dict[str, set[str]] = {}
    for bundle in bundle_manifest.get("bundles", []):
        name = bundle.get("name")
        files = bundle.get("files")
        if not isinstance(name, str) or not isinstance(files, list):
            raise ValueError("bundle manifest has incomplete bundle entry")
        bundles[name] = {item["path"] for item in files if isinstance(item, dict) and isinstance(item.get("path"), str)}
    if set(bundles) != set(ROLE_ROOTS):
        raise ValueError("bundle manifest must contain legacy, candidate and compact")
    return bundles


def run_observations(run_manifest: dict[str, Any]) -> dict[str, set[str]]:
    observed: dict[str, set[str]] = {name: set() for name in ROLE_ROOTS}
    for run in run_manifest.get("runs", []):
        bundle = run.get("bundle", {})
        name = bundle.get("name")
        fixture = run.get("fixture", {})
        fixture_class = fixture.get("class")
        if name in observed and isinstance(fixture_class, str) and run.get("execution_status") == "observed":
            observed[name].add(fixture_class)
    return observed


def cross_skill_observations(cross_skill: dict[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for item in cross_skill.get("results", []):
        name = item.get("bundle")
        if isinstance(name, str):
            result[name] = {
                field: str(item.get(field, {}).get("status", "missing"))
                for field in ("handoff", "submission", "digest", "revision")
            }
    return result


def feature_path(feature: dict[str, Any], bundle_name: str) -> str:
    role = feature.get("role")
    path = feature.get("path")
    try:
        return f"{ROLE_ROOTS[bundle_name][role]}/{path}"
    except KeyError as exc:
        raise ValueError(f"invalid feature role or bundle: {feature.get('feature_id')}") from exc


def decision_by_scope(decisions: dict[str, Any]) -> list[dict[str, Any]]:
    values = decisions.get("decisions", [])
    if not isinstance(values, list):
        raise ValueError("compatibility decisions must be a list")
    for item in values:
        if item.get("classification") not in CLASSIFICATIONS:
            raise ValueError(f"unsupported decision classification: {item.get('id')}")
        for required in ("id", "scope", "reason", "spec_ref", "evidence_ref"):
            if not isinstance(item.get(required), str) or not item[required]:
                raise ValueError(f"decision field is missing: {required}")
    return values


def classify_feature(
    feature: dict[str, Any],
    bundle_files: dict[str, set[str]],
    observations: dict[str, set[str]],
) -> dict[str, Any]:
    feature_id = feature["feature_id"]
    paths = {name: feature_path(feature, name) for name in ROLE_ROOTS}
    presence = {name: paths[name] in bundle_files[name] for name in ROLE_ROOTS}
    common = {"feature_id": feature_id, "role": feature["role"], "path": feature["path"], "presence": presence}

    if not feature.get("legacy_presence", False):
        return {
            **common,
            "classification": "intentional-noncompatibility",
            "status": "new-contract-feature",
            "reason": "Legacyに存在しない新規Contract機能であり、Legacy完全互換の欠落には数えない",
            "comparison_basis": "feature inventory legacy_presence=false",
        }

    missing = [name for name in ("candidate", "compact") if not presence[name]]
    if missing:
        return {
            **common,
            "classification": "missing-or-unverified",
            "status": "unverified",
            "reason": "Legacy互換対象の入口がCandidateまたはcompactに存在しない",
            "missing_bundles": missing,
            "comparison_basis": "bundle manifest path presence",
        }

    if feature.get("surface_type") == "documentation":
        return {
            **common,
            "classification": "compatible",
            "status": "observed",
            "reason": "三版Bundleに同一役割の公開文書入口が存在する",
            "comparison_basis": "bundle manifest path presence",
        }

    required_classes = {"golden", "negative", "cross-skill", "legacy-compat", "size"}
    missing_observation = {
        name: sorted(required_classes - observations.get(name, set()))
        for name in ("legacy", "candidate", "compact")
    }
    if any(missing_observation.values()):
        return {
            **common,
            "classification": "missing-or-unverified",
            "status": "unverified",
            "reason": "実行可能入口のfixture別Evidenceが不足している",
            "missing_fixture_classes": missing_observation,
            "comparison_basis": "run manifest execution_status",
        }
    return {
        **common,
        "classification": "missing-or-unverified",
        "status": "unverified",
        "reason": "実行結果は取得済みだが、機能ID単位の必須引数・終了コード・JSON項目の突合が未定義",
        "comparison_basis": "feature-level contract comparison is not defined",
    }


def build_report(
    inventory: dict[str, Any],
    bundle_manifest: dict[str, Any],
    run_manifest: dict[str, Any],
    cross_skill: dict[str, Any],
    decisions: dict[str, Any],
) -> dict[str, Any]:
    if inventory.get("schema_version") != "feature-surface-inventory-1" or inventory.get("feature_count") != 43:
        raise ValueError("feature surface inventory must contain 43 features")
    bundle_files = bundle_file_sets(bundle_manifest)
    observations = run_observations(run_manifest)
    cross = cross_skill_observations(cross_skill)
    feature_results = [classify_feature(feature, bundle_files, observations) for feature in inventory["features"]]
    classified_decisions = decision_by_scope(decisions)
    counts: dict[str, int] = {name: 0 for name in CLASSIFICATIONS}
    for item in feature_results:
        counts[item["classification"]] += 1
    for item in classified_decisions:
        counts[item["classification"]] += 1
    unresolved = counts["missing-or-unverified"]
    intentional = counts["intentional-noncompatibility"]
    if unresolved:
        overall = "evidence-gap"
    elif intentional:
        overall = "intentional-noncompatibility"
    else:
        overall = "observed"
    return {
        "schema_version": "compatibility-report-1",
        "overall_status": overall,
        "legacy_full_compatibility": False if intentional or unresolved else True,
        "classification_counts": counts,
        "inputs": {
            "inventory_schema": inventory["schema_version"],
            "bundle_manifest_schema": bundle_manifest.get("schema_version"),
            "run_manifest_id": run_manifest.get("run_id"),
            "cross_skill_run_id": cross_skill.get("run_id"),
        },
        "cross_skill": cross,
        "decisions": classified_decisions,
        "features": feature_results,
        "unverified_reasons": sorted({item["reason"] for item in feature_results if item["classification"] == "missing-or-unverified"}),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--bundle-manifest", type=Path, required=True)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--cross-skill", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_report(
            read_json(args.inventory),
            read_json(args.bundle_manifest),
            read_json(args.run_manifest),
            read_json(args.cross_skill),
            read_json(args.decisions),
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "overall_status": report["overall_status"], "classification_counts": report["classification_counts"]}, ensure_ascii=False))
    return 0 if report["overall_status"] == "observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
