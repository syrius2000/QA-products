"""Reviewer/Author入口から利用する共通CLI Facade。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runtime import BundleError, bundle_root, load_request, run, verify_manifest


def main(role: str, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=f"spec-driven-qa-{role}")
    parser.add_argument("operation")
    parser.add_argument("--json", dest="payload", default="{}")
    args = parser.parse_args(argv)
    try:
        root = bundle_root(Path(__file__))
        verify_manifest(root)
        result = run(role, args.operation, load_request(args.payload))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except BundleError as exc:
        print(json.dumps({"status": "error", "code": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
