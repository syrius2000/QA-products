#!/usr/bin/env python3
"""機能台帳へ実行契約の観測欄を付与し、スキーマを検証するCLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

STATUS_VALUES = {"observed", "not_applicable", "unverified"}
SURFACE_FIELDS = (
    "arguments", "expected_exit_codes", "json_required_fields",
    "state_effects", "side_effects",
)


def load_inventory(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "feature-inventory-1":
        raise ValueError("unsupported feature inventory schema")
    if data.get("feature_count") != len(data.get("features", [])):
        raise ValueError("feature count does not match rows")
    return data


def status_value(status: str, value: Any = None) -> dict[str, Any]:
    if status not in STATUS_VALUES:
        raise ValueError(f"unsupported surface status: {status}")
    return {"status": status, "value": value}


def build_surface(inventory: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for feature in inventory["features"]:
        is_executable = feature["path"].endswith(".py")
        status = "unverified" if is_executable else "not_applicable"
        surface = {field: status_value(status, [] if status == "not_applicable" else None) for field in SURFACE_FIELDS}
        rows.append({**feature, "surface_type": "executable" if is_executable else "documentation", "contract_surface": surface})
    result = {
        "schema_version": "feature-surface-inventory-1",
        "source_inventory": inventory["source"],
        "feature_count": len(rows),
        "legacy_compatible_count": inventory["legacy_compatible_count"],
        "new_contract_feature_count": inventory["new_contract_feature_count"],
        "features": rows,
    }
    validate_surface(result)
    return result


def validate_surface(data: dict[str, Any]) -> None:
    rows = data.get("features", [])
    if data.get("feature_count") != len(rows) or data.get("feature_count") != 43:
        raise ValueError("surface inventory must contain exactly 43 features")
    ids = [row.get("feature_id") for row in rows]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise ValueError("surface inventory contains duplicate or empty feature ids")
    for row in rows:
        if row.get("surface_type") not in {"documentation", "executable"}:
            raise ValueError(f"invalid surface type: {row.get('feature_id')}")
        surface = row.get("contract_surface")
        if set(surface or {}) != set(SURFACE_FIELDS):
            raise ValueError(f"incomplete contract surface: {row.get('feature_id')}")
        for field in SURFACE_FIELDS:
            entry = surface[field]
            if entry.get("status") not in STATUS_VALUES or "value" not in entry:
                raise ValueError(f"invalid contract field: {row.get('feature_id')}:{field}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = build_surface(load_inventory(args.inventory))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "feature_count": result["feature_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
