import json
import subprocess
import sys
from pathlib import Path

STAGE_DIR = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def test_reviewer_launcher_help():
    launcher_path = STAGE_DIR / "spec-driven-qa-review" / "launcher.py"
    res = subprocess.run(
        [PYTHON, str(launcher_path), "--help"],
        capture_output=True,
        text=True,
        cwd=str(STAGE_DIR),
    )
    assert res.returncode == 0
    assert "reviewer" in res.stdout or "operation" in res.stdout


def test_reviewer_launcher_cli_init_case(tmp_path):
    launcher_path = STAGE_DIR / "spec-driven-qa-review" / "launcher.py"
    payload = {
        "action": "init",
        "case_id": "QA-0801-cli-test",
        "target": "src/module.py",
        "purpose": "docs/purpose.md",
        "profile": "standard",
        "qa_root": str(tmp_path),
    }
    res = subprocess.run(
        [PYTHON, str(launcher_path), "review", "--json", json.dumps(payload)],
        capture_output=True,
        text=True,
        cwd=str(STAGE_DIR),
    )
    assert res.returncode == 0
    out = json.loads(res.stdout.strip())
    assert out["status"] == "success"
    assert out["case_id"] == "QA-0801-cli-test"
    assert (tmp_path / "QA-0801-cli-test" / "review.md").exists()


def test_reviewer_launcher_missing_shared_core(tmp_path):
    # Launch in a directory lacking shared_core
    launcher_path = STAGE_DIR / "spec-driven-qa-review" / "launcher.py"
    fake_skill_dir = tmp_path / "spec-driven-qa-review"
    fake_skill_dir.mkdir(parents=True)
    (fake_skill_dir / "launcher.py").write_text((launcher_path).read_text(encoding="utf-8"), encoding="utf-8")
    
    res = subprocess.run(
        [PYTHON, str(fake_skill_dir / "launcher.py"), "review", "--json", "{}"],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert res.returncode == 2
    out = json.loads(res.stderr.strip())
    assert out["status"] == "error"
    assert out["code"] == "shared_core_missing"
