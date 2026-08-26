#!/usr/bin/env python3
"""Agent／Run単位の外部AI Evidenceを混同せず集計する標準ライブラリCLI。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SECRET = re.compile(r"(?i)(?:bearer\s+[A-Za-z0-9._-]{8,}|(?<![A-Za-z0-9_])(?:api[_-]?key|token|password|secret)\b\s*[:=]\s*(?!(?:unverified|unknown|not-assessable|none|masked)\b)[A-Za-z0-9][A-Za-z0-9._+/=-]{7,}|\b(?:sk|ghp)_[A-Za-z0-9_-]{8,}\b)")
UNVERIFIED = {None, "unverified", "not-assessable", "unknown"}


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object is required: {path}")
    return value


def contains_secret(value: Any) -> bool:
    if isinstance(value, str):
        return bool(SECRET.search(value))
    if isinstance(value, dict):
        return any(contains_secret(key) or contains_secret(item) for key, item in value.items())
    if isinstance(value, list):
        return any(contains_secret(item) for item in value)
    return False


def metric_status(value: Any) -> str:
    if value is None:
        return "unverified"
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized or normalized in UNVERIFIED:
            return "unverified"
    return "observed"


def field_status(manifest: dict[str, Any], results_path: Path) -> dict[str, str]:
    """異なるAgentのmanifest名を勝手に同一視せず、別名対応と欠測を記録する。"""
    def known(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            normalized = value.strip()
            return bool(normalized) and normalized not in UNVERIFIED
        return True

    timing = (
        known(manifest.get("started_at")) and known(manifest.get("ended_at"))
    ) or (
        known(manifest.get("start_time")) and known(manifest.get("end_time"))
    )
    cases = all(known(manifest.get(key)) for key in ("cases_total", "executed_cases", "unexecuted_cases"))
    cases = cases or all(known(manifest.get(key)) for key in ("executed_cases", "not_run_cases"))
    digest = any(
        isinstance(value, dict)
        and any("digest" in str(key).lower() and known(item) for key, item in value.items())
        for value in manifest.get("bundles", {}).values()
    ) if isinstance(manifest.get("bundles"), dict) else False
    digest = digest or any(
        key.endswith("_bundle_digest") and known(value)
        for key, value in manifest.items()
    )
    condition = known(manifest.get("model")) and any(
        known(manifest.get(key)) for key in ("model_settings", "environment", "context_isolation")
    )
    return {
        "prompt_suite": "observed" if any(known(manifest.get(key)) for key in ("prompt_suite_digest", "prompt_suite_sha256")) else "unverified",
        "output": "observed" if results_path.is_file() and results_path.stat().st_size > 0 else "unverified",
        "conditions": "observed" if condition else "unverified",
        "timing": "observed" if timing else "unverified",
        "execution_count": "observed" if cases else "unverified",
        "bundle_digest": "observed" if digest else "unverified",
        "results": "observed" if results_path.is_file() else "unverified",
        "unexecuted_items": "observed" if any(known(manifest.get(key)) for key in ("unexecuted_cases", "not_run_cases")) else "unverified",
    }


def discover_runs(root: Path) -> list[tuple[Path, Path, Path]]:
    runs = []
    for manifest_path in sorted(root.glob("*/**/manifest.json")):
        run_dir = manifest_path.parent
        agent_dir = run_dir.parent
        if agent_dir.parent != root:
            continue
        results_path = run_dir / "results.json"
        runs.append((agent_dir, run_dir, results_path))
    return runs


def summarize_run(agent_dir: Path, run_dir: Path, results_path: Path) -> dict[str, Any]:
    manifest = read_json(run_dir / "manifest.json")
    results = read_json(results_path) if results_path.is_file() else {}
    if contains_secret(manifest) or contains_secret(results):
        raise ValueError("secret detected in Agent/Run Evidence; values were not retained")
    agent_id = manifest.get("agent_id")
    run_id = manifest.get("run_id")
    if not isinstance(agent_id, str) or not agent_id or agent_id != agent_dir.name:
        raise ValueError("agent_id does not match Evidence directory")
    if not isinstance(run_id, str) or not run_id or run_id != run_dir.name:
        raise ValueError("run_id does not match Evidence directory")
    if results:
        result_pairs = []
        if "agent_id" in results or "run_id" in results:
            result_pairs.append((results.get("agent_id"), results.get("run_id")))
        nested_results = results.get("results")
        if isinstance(nested_results, list):
            result_pairs.extend(
                (item.get("agent_id"), item.get("run_id"))
                for item in nested_results
                if isinstance(item, dict) and ("agent_id" in item or "run_id" in item)
            )
        if result_pairs and any(pair != (agent_id, run_id) for pair in result_pairs):
            raise ValueError("manifest and results identify different Agent/Run")
    aggregate = manifest.get("aggregate", {})
    metrics = {
        "input_tokens": metric_status(aggregate.get("candidate", {}).get("avg_input_tokens")),
        "output_tokens": metric_status(aggregate.get("candidate", {}).get("avg_output_tokens")),
        "total_tokens": metric_status(aggregate.get("candidate", {}).get("avg_tokens")),
        "latency": metric_status(aggregate.get("candidate", {}).get("avg_latency")),
    }
    completeness = field_status(manifest, results_path)
    return {
        "agent_id": agent_id,
        "run_id": run_id,
        "model": manifest.get("model", {"name": "unknown", "status": "unverified"}),
        "started_at": manifest.get("started_at"),
        "ended_at": manifest.get("ended_at"),
        "prompt_suite_digest": manifest.get("prompt_suite_digest"),
        "bundle_digests": {name: value.get("zip_digest") for name, value in manifest.get("bundles", {}).items() if isinstance(value, dict)},
        "cases_total": manifest.get("cases_total"),
        "executed_cases": manifest.get("executed_cases"),
        "unexecuted_cases": manifest.get("unexecuted_cases"),
        "self_scored": manifest.get("self_scored"),
        "pytest": manifest.get("pytest", {"status": "unverified"}),
        "metrics": metrics,
        "required_field_status": completeness,
        "required_fields_complete": all(value == "observed" for value in completeness.values()),
        "source_evidence": str(run_dir.relative_to(root_for_source(run_dir))),
    }


def root_for_source(run_dir: Path) -> Path:
    return run_dir.parents[1]


def build_report(root: Path) -> dict[str, Any]:
    if not root.is_dir():
        raise ValueError(f"Agent Evidence directory does not exist: {root}")
    runs = discover_runs(root)
    if not runs:
        raise ValueError("no Agent/Run manifests found")
    entries = []
    errors = []
    seen: set[tuple[str, str]] = set()
    for agent_dir, run_dir, results_path in runs:
        try:
            entry = summarize_run(agent_dir, run_dir, results_path)
            key = (entry["agent_id"], entry["run_id"])
            if key in seen:
                errors.append("duplicate Agent/Run identifier")
            seen.add(key)
            entries.append(entry)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
    metric_values = [entry["metrics"] for entry in entries]
    field_values = [entry["required_field_status"] for entry in entries]
    status = "evidence-gap" if errors or len(entries) != len(runs) else "observed-with-unverified"
    return {
        "schema_version": "agent-evidence-aggregate-1",
        "status": status,
        "agent_count": len({entry["agent_id"] for entry in entries}),
        "run_count": len(entries),
        "agent_runs": entries,
        "metric_policy": "取得不能なToken・Latency・正答率はunverifiedのまま保持し、他Agentの値で補完しない",
        "metric_status_summary": {
            "input_tokens": sorted({item["input_tokens"] for item in metric_values}),
            "output_tokens": sorted({item["output_tokens"] for item in metric_values}),
            "total_tokens": sorted({item["total_tokens"] for item in metric_values}),
            "latency": sorted({item["latency"] for item in metric_values}),
        },
        "required_field_status_summary": {
            field: {
                "observed": sum(item[field] == "observed" for item in field_values),
                "unverified": sum(item[field] == "unverified" for item in field_values),
            }
            for field in field_values[0]
        } if field_values else {},
        "required_fields_policy": "項目名の別名は限定的に対応し、存在を確認できないPrompt・出力・条件・時刻・件数・digest・結果・未実行項目はunverifiedとする",
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents-root", type=Path)
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if bool(args.agents_root) == bool(args.source_manifest):
            raise ValueError("exactly one of --agents-root or --source-manifest is required")
        source_manifest = None
        if args.source_manifest:
            from agent_source_manifest import verify_manifest

            agents_root = verify_manifest(args.source_manifest.resolve())
            source_manifest = args.source_manifest.resolve()
        else:
            agents_root = args.agents_root.resolve()
        report = build_report(agents_root)
        if source_manifest:
            repository = next(
                (parent for parent in (source_manifest.parent, *source_manifest.parents) if (parent / "AGENTS.md").is_file()),
                None,
            )
            report["source_manifest"] = (
                source_manifest.relative_to(repository).as_posix() if repository else str(source_manifest)
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": report["status"], "agent_count": report["agent_count"], "run_count": report["run_count"]}, ensure_ascii=False))
    return 0 if report["status"] == "observed-with-unverified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
