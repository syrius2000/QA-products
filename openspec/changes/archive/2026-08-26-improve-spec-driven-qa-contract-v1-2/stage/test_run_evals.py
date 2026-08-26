import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_evals import run_evals


def test_fixed_eval_groups_are_declared_and_pass(tmp_path: Path):
    result = run_evals(ROOT, [sys.executable, "-c", "print('fixture pass')"])
    assert result["ok"] is True
    assert "cross-skill" in result["groups"]
    assert "legacy-contract" in result["groups"]
