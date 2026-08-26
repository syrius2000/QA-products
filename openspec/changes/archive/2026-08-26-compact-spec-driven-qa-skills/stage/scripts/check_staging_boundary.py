#!/usr/bin/env python3
"""staging Manifestの書込み境界を検査する。対象外へ書き込まないdry-run用。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    allowed = (manifest_path.parent / data["allowed_write_root"]).resolve()
    if not allowed.is_relative_to(manifest_path.parent.resolve()):
        raise SystemExit("FAIL-CLOSED: allowed_write_root escapes staging root")
    external = [Path(value).resolve() for value in data["external_targets"].values()]
    overlap = [str(path) for path in external if path == allowed or allowed.is_relative_to(path)]
    if overlap:
        raise SystemExit(f"FAIL-CLOSED: external target overlaps write root: {overlap}")
    if data["backup"]["status"] != "not-created" or not data["backup"]["required_before_external_deploy"]:
        raise SystemExit("FAIL-CLOSED: backup gate is not defined")
    if data["rollback"]["status"] != "design-only" or not data["rollback"]["required_before_external_deploy"]:
        raise SystemExit("FAIL-CLOSED: rollback gate is not defined")
    print(json.dumps({
        "status": "dry-run-safe",
        "allowed_write_root": str(allowed),
        "external_targets": [str(path) for path in external],
        "writes_performed": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
