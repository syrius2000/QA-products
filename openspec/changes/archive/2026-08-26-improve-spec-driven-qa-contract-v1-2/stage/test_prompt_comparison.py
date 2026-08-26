import json
from pathlib import Path

from prompt_comparison import build_report


ROOT = Path(__file__).resolve().parent


def test_prompt_comparison_is_explicitly_unverified_without_external_ai(tmp_path: Path):
    report = build_report(ROOT)
    assert report["status"] == "unverified"
    assert report["prompt_count"] > 0
    assert report["metrics"]["accuracy"] is None
    assert report["safety_checks"]["self_close"] == "unverified"
