#!/usr/bin/env python3
"""Legacy基準台帳から公開・実行可能機能を抽出し検証するCLI。"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

ROLE_ROOTS = {"reviewer": "spec-driven-qa-review", "author": "spec-driven-qa-author-response"}
REQUIRED_FIELDS = {
    "feature_id", "role", "category", "path", "lines", "bytes", "sha256",
    "public_or_runtime_entry", "notes",
}


def repository_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "AGENTS.md").is_file() and (parent / "openspec").is_dir():
            return parent
    raise RuntimeError("repository root could not be resolved")


def default_inventory() -> Path:
    return repository_root() / "openspec/changes/archive/2026-08-26-compact-spec-driven-qa-skills/stage/baseline/feature_inventory.tsv"


def read_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if set(reader.fieldnames or ()) != REQUIRED_FIELDS:
            raise ValueError("feature inventory columns do not match the required schema")
        rows = []
        for row in reader:
            if row["public_or_runtime_entry"] != "True":
                continue
            rows.append({
                "feature_id": row["feature_id"],
                "role": row["role"],
                "category": row["category"],
                "path": row["path"],
                "lines": int(row["lines"]),
                "bytes": int(row["bytes"]),
                "sha256": row["sha256"],
                "public_or_runtime_entry": True,
                "notes": row["notes"],
                "comparison_class": "legacy-public-runtime",
            })
    return rows


def validate_rows(rows: list[dict[str, Any]], legacy_zip: Path) -> list[str]:
    if len(rows) != 43:
        raise ValueError(f"expected 43 public/runtime features, got {len(rows)}")
    ids = [row["feature_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate feature id")
    if any(row["role"] not in ROLE_ROOTS for row in rows):
        raise ValueError("unknown feature role")
    with zipfile.ZipFile(legacy_zip) as archive:
        names = {info.filename.rstrip("/") for info in archive.infolist() if not info.is_dir()}
    missing = []
    for row in rows:
        expected = f"{ROLE_ROOTS[row['role']]}/{row['path']}"
        if expected not in names:
            missing.append(expected)
    # The ledger is the union of public features across versions. Legacy
    # absence is retained as a new-feature classification by build_inventory.
    return missing


def build_inventory(inventory_path: Path | None = None, legacy_zip: Path | None = None) -> dict[str, Any]:
    root = repository_root()
    inventory_path = inventory_path or default_inventory()
    legacy_zip = legacy_zip or root / "archives/skills/legacy-qa-skills_20260825.zip"
    rows = read_rows(inventory_path)
    validate_rows(rows, legacy_zip)
    with zipfile.ZipFile(legacy_zip) as archive:
        names = {info.filename.rstrip("/") for info in archive.infolist() if not info.is_dir()}
    for row in rows:
        expected = f"{ROLE_ROOTS[row['role']]}/{row['path']}"
        row["legacy_presence"] = expected in names
        row["comparison_class"] = "legacy-compatible" if row["legacy_presence"] else "new-contract-feature"
    return {
        "schema_version": "feature-inventory-1",
        "source": str(inventory_path.resolve().relative_to(root)),
        "legacy_bundle": str(legacy_zip.resolve().relative_to(root)),
        "feature_count": len(rows),
        "legacy_compatible_count": sum(row["legacy_presence"] for row in rows),
        "new_contract_feature_count": sum(not row["legacy_presence"] for row in rows),
        "features": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--legacy-zip", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = build_inventory(args.inventory, args.legacy_zip)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "feature_count": result["feature_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
