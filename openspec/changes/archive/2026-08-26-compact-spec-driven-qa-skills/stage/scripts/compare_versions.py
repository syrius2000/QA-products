#!/usr/bin/env python3
"""3版の構造化結果を仕様正本に照らして比較する。標準ライブラリのみ。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RELEVANT_FIELDS = ("exit_code", "contract", "state", "side_effects")


def normalize(result: dict) -> dict:
    return {key: result.get(key) for key in RELEVANT_FIELDS}


def compare(payload: dict) -> dict:
    authority = payload["authority"]
    results = payload["results"]
    decisions = []
    for case in payload["cases"]:
        case_id = case["id"]
        expected = case["expected"]
        case_results = {version: normalize(results[version][case_id]) for version in results}
        spec_failures = [version for version in results if not results[version][case_id].get("spec_compliant", False)]
        contract_match = len({json.dumps(value, sort_keys=True) for value in case_results.values()}) == 1
        expected_match = [version for version, result in results.items() if normalize(result[case_id]) == expected]
        decisions.append({
            "id": case_id,
            "authority": authority,
            "spec_violations": spec_failures,
            "contract_match": contract_match,
            "expected_match_versions": expected_match,
            "results": case_results,
            "decision": "nonconformant" if spec_failures else ("equivalent" if contract_match else "behavior-diff"),
        })
    return {
        "schema_version": "comparison-report-1",
        "authority": authority,
        "candidate_behavior_is_not_authority": True,
        "decisions": decisions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = compare(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "decisions": len(report["decisions"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
