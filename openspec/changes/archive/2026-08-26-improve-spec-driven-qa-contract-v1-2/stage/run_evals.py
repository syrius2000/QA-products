#!/usr/bin/env python3
"""Contract v1.2の固定fixtureを一括評価する。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


EVAL_GROUPS = {
    "normal": "test_contract_v1_2.py test_digest.py test_evidence.py",
    "negative": "test_handoff_validator.py test_state_machine.py test_terminal_record.py",
    "conflict": "test_freshness.py test_submission_validator.py",
    "cross-skill": "test_handoff_submission.py test_submission_store.py",
    "legacy-contract": "test_legacy_adapter.py",
    "fast-path": "test_execution_policy.py",
    "evidence-gap": "test_evidence.py test_link_validator.py test_secret_guard.py",
}


def run_evals(stage: Path, pytest_command: list[str] | None = None) -> dict[str, object]:
    command = pytest_command or [sys.executable, "-m", "pytest", "-q", "spec_driven_qa_reviewer/tests", "spec_driven_qa_author_response/tests"]
    result = subprocess.run(command, cwd=stage, text=True, capture_output=True, check=False)
    return {
        "ok": result.returncode == 0,
        "status": "passed" if result.returncode == 0 else "failed",
        "groups": sorted(EVAL_GROUPS),
        "pytest_exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run fixed Contract v1.2 evaluation fixtures")
    parser.add_argument("--stage", type=Path, default=Path(__file__).parent)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    result = run_evals(args.stage)
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    else:
        print(f"Contract v1.2 evals: {result['status']}")
        print(result["stdout"], end="")
        if result["stderr"]:
            print(result["stderr"], file=sys.stderr, end="")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
