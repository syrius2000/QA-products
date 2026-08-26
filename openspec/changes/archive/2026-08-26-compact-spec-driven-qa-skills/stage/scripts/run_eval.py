"""3版比較とfixture層の存在を一括評価する。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from compare_versions import compare


REQUIRED_FIXTURES = {
    "golden": "golden",
    "negative": "negative",
    "cross_skill": "cross-skill",
    "legacy": "legacy",
    "size": "size",
}


def evaluate(root: Path) -> dict:
    fixture_root = root / "fixtures"
    sample = json.loads((fixture_root / "comparison/sample-results.json").read_text(encoding="utf-8"))
    report = compare(sample)
    layers = {name: (fixture_root / directory).is_dir() and any((fixture_root / directory).iterdir()) for name, directory in REQUIRED_FIXTURES.items()}
    report["fixture_layers"] = layers
    report["fixture_layers_complete"] = all(layers.values())
    report["diagnostic_differences"] = []
    report["contract_differences"] = [item["id"] for item in report["decisions"] if item["decision"] == "behavior-diff"]
    report["legacy_compatibility_differences"] = report["contract_differences"]
    report["status"] = "ok" if report["fixture_layers_complete"] else "incomplete-fixtures"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = evaluate(args.root)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "decisions": len(result["decisions"]), "fixture_layers_complete": result["fixture_layers_complete"]}, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
