#!/usr/bin/env python3
"""2 Skillの読み取り専用ベースライン台帳と計測結果を作成する。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from measure_size import iter_files, line_count, measure  # noqa: E402


def role_slug(role: str) -> str:
    return "reviewer" if role == "spec-driven-qa-review" else "author"


def feature_id(role: str, relative: Path) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", relative.as_posix()).strip("_").upper()
    return f"{role_slug(role)}:{value}"


def build_inventory(role: str, root: Path) -> list[dict]:
    rows = []
    for path in iter_files(root, None):
        relative = path.relative_to(root)
        data = path.read_bytes()
        first = relative.parts[0] if len(relative.parts) > 1 else "root"
        public = relative.name in {"SKILL.md", "README.md", "INSTALL.md"} or first in {"scripts", "templates"}
        rows.append(
            {
                "feature_id": feature_id(role, relative),
                "role": role_slug(role),
                "category": first,
                "path": relative.as_posix(),
                "lines": line_count(data),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "public_or_runtime_entry": public,
                "notes": "公開入口または実行資産" if public else "配布・検証資産",
            }
        )
    return rows


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compare_mirror(canonical_roles: dict[str, Path], mirror_root: Path | None) -> dict:
    if mirror_root is None:
        return {"status": "not-requested", "roles": {}}
    roles = {}
    for role, canonical in canonical_roles.items():
        mirror = mirror_root / role
        canonical_files = {p.relative_to(canonical).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in iter_files(canonical, None)}
        mirror_files = {p.relative_to(mirror).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in iter_files(mirror, None)} if mirror.is_dir() else {}
        missing = sorted(set(canonical_files) - set(mirror_files))
        extra = sorted(set(mirror_files) - set(canonical_files))
        changed = sorted(path for path in set(canonical_files) & set(mirror_files)
                         if canonical_files[path] != mirror_files[path])
        roles[role] = {
            "canonical_root": str(canonical),
            "mirror_root": str(mirror),
            "status": "identical" if not (missing or extra or changed) else "different",
            "missing": missing,
            "extra": extra,
            "changed": changed,
        }
    return {"status": "identical" if all(v["status"] == "identical" for v in roles.values()) else "different", "roles": roles}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer-root", required=True, type=Path)
    parser.add_argument("--author-root", required=True, type=Path)
    parser.add_argument("--mirror-root", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    roles = {
        "spec-driven-qa-review": args.reviewer_root.resolve(),
        "spec-driven-qa-author-response": args.author_root.resolve(),
    }
    metrics = {role: measure(root) for role, root in roles.items()}
    inventory = []
    for role, root in roles.items():
        inventory.extend(build_inventory(role, root))
    inventory.sort(key=lambda row: (row["role"], row["path"]))
    write_json(output / "baseline_metrics.json", {
        "schema_version": "baseline-1",
        "source": "read-only",
        "canonical_roots": {role: str(root) for role, root in roles.items()},
        "skills": metrics,
        "total": {
            "files": sum(item["counts"]["files"] for item in metrics.values()),
            "bytes": sum(item["counts"]["bytes"] for item in metrics.values()),
            "lines": sum(item["counts"]["lines"] for item in metrics.values()),
        },
    })
    write_json(output / "baseline_inventory.json", {
        "schema_version": "feature-inventory-1",
        "source": "read-only",
        "rows": inventory,
    })
    (output / "feature_inventory.tsv").write_text(
        "feature_id\trole\tcategory\tpath\tlines\tbytes\tsha256\tpublic_or_runtime_entry\tnotes\n"
        + "\n".join(
            "\t".join(str(row[key]) for key in (
                "feature_id", "role", "category", "path", "lines", "bytes", "sha256", "public_or_runtime_entry", "notes"
            )) for row in inventory
        )
        + "\n",
        encoding="utf-8",
    )
    write_json(output / "mirror_comparison.json", compare_mirror(roles, args.mirror_root.resolve() if args.mirror_root else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
