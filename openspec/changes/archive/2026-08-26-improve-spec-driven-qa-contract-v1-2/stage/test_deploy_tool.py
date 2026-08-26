import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from deploy_tool import SafetyError, create_backup, deployment_plan, rollback


def make_bundle(root: Path, reviewer_text: str = "new reviewer\n") -> Path:
    (root / "spec_driven_qa_reviewer").mkdir(parents=True)
    (root / "spec_driven_qa_author_response").mkdir(parents=True)
    (root / "spec_driven_qa_reviewer" / "SKILL.md").write_text(reviewer_text, encoding="utf-8")
    (root / "spec_driven_qa_author_response" / "SKILL.md").write_text("new author\n", encoding="utf-8")
    (root / "spec_driven_qa_reviewer" / ".pytest_cache").mkdir()
    (root / "spec_driven_qa_reviewer" / ".pytest_cache" / "must-ignore").write_text("cache", encoding="utf-8")
    return root


def test_plan_is_dry_run_and_ignores_cache(tmp_path: Path):
    source = make_bundle(tmp_path / "source")
    target = tmp_path / "target"
    (target / "spec-driven-qa-review").mkdir(parents=True)
    (target / "spec-driven-qa-review" / "SKILL.md").write_text("old reviewer\n", encoding="utf-8")
    result = deployment_plan(source, target)
    actions = {(item["role"], item["path"]): item["action"] for item in result["changes"]}
    assert actions[("spec-driven-qa-review", "SKILL.md")] == "replace"
    assert all(".pytest_cache" not in item["path"] for item in result["changes"])
    assert (target / "spec-driven-qa-review" / "SKILL.md").read_text() == "old reviewer\n"


def test_backup_and_rollback_restore_previous_state(tmp_path: Path):
    target = tmp_path / "target"
    (target / "spec-driven-qa-review").mkdir(parents=True)
    original = target / "spec-driven-qa-review" / "SKILL.md"
    original.write_text("original\n", encoding="utf-8")
    backup = tmp_path / "backup"
    manifest = create_backup(target, backup)
    assert manifest["status"] == "COMPLETE"
    original.write_text("changed\n", encoding="utf-8")
    preview = rollback(target, backup, apply=False, confirmation=None)
    assert preview["status"] == "DRY-RUN"
    result = rollback(target, backup, apply=True, confirmation=str(target.resolve()))
    assert result["status"] == "COMPLETE"
    assert original.read_text() == "original\n"


def test_rollback_requires_exact_confirmation(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    backup = tmp_path / "backup"
    create_backup(target, backup)
    with pytest.raises(SafetyError):
        rollback(target, backup, apply=True, confirmation="/wrong/target")
