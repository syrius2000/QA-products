#!/usr/bin/env python3
"""機能台帳と比較fixtureの対応を生成・検証する標準ライブラリCLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CLASSES = ("golden", "negative", "cross-skill", "legacy-compat", "size")


def build_index(inventory_path: Path) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if inventory.get("schema_version") != "feature-surface-inventory-1":
        raise ValueError("unsupported surface inventory schema")
    features = inventory.get("features", [])
    if len(features) != 43 or len({item.get("feature_id") for item in features}) != 43:
        raise ValueError("fixture index requires 43 unique features")
    return {
        "schema_version": "fixture-index-1",
        "classes": {
            name: {"fixture": f"fixtures/{name}.json", "feature_ids": [item["feature_id"] for item in features]}
            for name in CLASSES
        },
        "feature_count": len(features),
    }


def validate_index(index: dict) -> None:
    if index.get("schema_version") != "fixture-index-1" or set(index.get("classes", {})) != set(CLASSES):
        raise ValueError("fixture index classes are incomplete")
    if index.get("feature_count") != 43:
        raise ValueError("fixture index must cover 43 features")
    ids = [item for data in index["classes"].values() for item in data["feature_ids"]]
    if len(ids) != 43 * len(CLASSES) or any(not item for item in ids):
        raise ValueError("fixture index feature mapping is incomplete")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = build_index(args.inventory)
        validate_index(result)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "classes": list(CLASSES), "feature_count": 43}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
