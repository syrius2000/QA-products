import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))

from spec_driven_qa_reviewer.scripts.openspec_bridge import collect_baseline


def test_baseline_records_path_revision_digest_and_evidence_policy(tmp_path: Path):
    outputs = {
        ("openspec", "status"): '{"changeRoot":"/repo/openspec/changes/demo","valid":true,"tasks":[{"done":true}]}' ,
        ("git", "rev-parse"): "abc123",
    }

    def fake_run(args, cwd):
        if args[:2] == ["openspec", "status"]:
            return outputs[("openspec", "status")]
        return outputs[("git", "rev-parse")]

    with patch("spec_driven_qa_reviewer.scripts.openspec_bridge._run", side_effect=fake_run), patch(
        "spec_driven_qa_reviewer.scripts.openspec_bridge.subprocess.check_output", return_value=b"diff"
    ):
        baseline = collect_baseline(tmp_path, "demo")
    assert baseline["change_root"].endswith("/demo")
    assert baseline["git_revision"] == "abc123"
    assert baseline["working_tree_digest"]
    assert baseline["evidence_policy"]["openspec_task_status_is_implementation_evidence"] is False
    assert baseline["evidence_policy"]["openspec_valid_true_is_implementation_evidence"] is False
