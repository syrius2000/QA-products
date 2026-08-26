#!/usr/bin/env python3
"""三版Bundleのファイル数・行数・バイト数を決定論的に計測するCLI。"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

import parity_harness


REQUIRED_PATHS = {
    "legacy": [
        "spec-driven-qa-review/SKILL.md",
        "spec-driven-qa-author-response/SKILL.md",
        "spec-driven-qa-author-response/tests/test_author_response.py",
    ],
    "candidate": [
        "bundle_validator.py",
        "spec_driven_qa_reviewer/SKILL.md",
        "spec_driven_qa_reviewer/tests/test_state_machine.py",
        "spec_driven_qa_reviewer/tests/test_submission_validator.py",
        "spec_driven_qa_author_response/tests/test_execution_policy.py",
    ],
    "compact": [
        "MANIFEST.json",
        "SPEC.md",
        "schemas/contract.json",
        "shared_core/chain.py",
        "shared_core/runtime.py",
        "shared_core/guards.py",
        "shared_core/secrets.py",
        "spec-driven-qa-review/SKILL.md",
        "spec-driven-qa-author-response/SKILL.md",
    ],
}


def line_count(data: bytes) -> int:
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def bundle_data(bundle: dict[str, Any], source: Path):
    if bundle["kind"] == "directory":
        for item in bundle["files"]:
            yield item["path"], (source / item["path"]).read_bytes()
        return
    with zipfile.ZipFile(source) as archive:
        for item in bundle["files"]:
            yield item["path"], archive.read(item["path"])


def stage_artifacts(stage_root: Path) -> dict[str, Any]:
    tests = sorted((stage_root / "tests").glob("test_*.py"))
    return {
        "stage_spec_present": (stage_root / "spec-driven-qa-bundle" / "SPEC.md").is_file(),
        "stage_safety_regression_present": (stage_root / "safety_regression.py").is_file(),
        "stage_tests_present": bool(tests),
        "stage_test_file_count": len(tests),
    }


def build_report(stage_root: Path) -> dict[str, Any]:
    config_path, config = parity_harness.load_config()
    manifest = parity_harness.build_manifest()
    by_name = {item["name"]: item for item in manifest["bundles"]}
    bundles = []
    for name in sorted(config["bundles"]):
        bundle = by_name[name]
        source = parity_harness.resolve_source(config_path, config["bundles"][name]["source"])
        records = list(bundle_data(bundle, source))
        paths = {path for path, _ in records}
        required = REQUIRED_PATHS[name]
        totals = {
            "file_count": len(records),
            "line_count": sum(line_count(data) for _, data in records),
            "byte_count": sum(len(data) for _, data in records),
        }
        bundles.append(
            {
                "name": name,
                "version": bundle["version"],
                "kind": bundle["kind"],
                "source_sha256": bundle["source_sha256"],
                **totals,
                "line_target": {"threshold": 1760, "within_threshold": totals["line_count"] <= 1760},
                "required_paths": [
                    {"path": path, "present": path in paths} for path in required
                ],
                "required_paths_present": all(path in paths for path in required),
            }
        )
    artifacts = stage_artifacts(stage_root)
    return {
        "schema_version": "size-report-1",
        "status": "observed",
        "measurement_policy": "Manifestで固定したBundle内容を再読込し、改行とUTF-8を推測せずバイト列から行数を算出する",
        "bundles": bundles,
        "integrity_checks": {
            **artifacts,
            "safety_functions_and_tests_preserved": all(
                item["required_paths_present"] for item in bundles
            ) and all(artifacts.values()),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = build_report(Path(__file__).resolve().parent)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "status": report["status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
