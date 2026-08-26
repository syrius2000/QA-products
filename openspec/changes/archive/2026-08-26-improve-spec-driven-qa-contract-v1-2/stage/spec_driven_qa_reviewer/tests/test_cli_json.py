import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT.parent


def run(module, *args):
    return subprocess.run(
        [sys.executable, "-m", module, *map(str, args)],
        cwd=STAGE,
        env={"PYTHONPATH": str(STAGE), "PATH": "/usr/bin:/bin"},
        text=True,
        capture_output=True,
        check=False,
    )


def test_marker_scan_json_has_common_fields(tmp_path: Path):
    result = run("spec_driven_qa_reviewer.scripts.detect_unresolved_markers", tmp_path, "--json")
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["ok"] is True
    assert {"schema_version", "ok", "status", "case_id", "next_action", "errors"} <= payload.keys()
    assert result.stderr == ""


def test_review_validation_json_reports_blocked_case(tmp_path: Path):
    result = run("spec_driven_qa_reviewer.scripts.validate_review_case", tmp_path, "--json")
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["status"] == "not-found"
    assert result.stderr == ""
