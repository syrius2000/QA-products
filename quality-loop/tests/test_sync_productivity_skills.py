from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sync_productivity_skills.py"
SOURCE = ROOT / "quality-loop" / "skills"


class SkillSyncDryRunTests(unittest.TestCase):
    def test_quality_qa_runtime_tracks_the_authoritative_modules(self):
        source = ROOT / "quality-loop" / "qa_workflow"
        runtime = SOURCE / "quality-qa" / "runtime" / "qa_workflow"
        for name in ["cli.py", "gitops.py", "review.py", "store.py", "workflow.py"]:
            with self.subTest(name=name):
                self.assertEqual((source / name).read_bytes(), (runtime / name).read_bytes())

    def prepare_destination(self, destination: Path) -> Path:
        subprocess.run(["git", "-C", str(destination), "init", "-b", "main"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(destination), "remote", "add", "origin", "https://github.com/syrius2000/Productivity-Skill.git"], check=True, capture_output=True)
        skills = destination / ".agents" / "skills"
        skills.mkdir(parents=True)
        return skills

    def test_dry_run_lists_unified_skill_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "Productivity-Skill"
            destination.mkdir()
            (destination / "README.md").write_text("Productivity-Skill\n")
            self.prepare_destination(destination)
            before = subprocess.run(["git", "-C", str(destination), "status", "--porcelain", "--untracked-files=all"], check=True, capture_output=True, text=True).stdout
            result = subprocess.run(["python3", str(SCRIPT), "--destination", str(destination), "--dry-run"], capture_output=True, text=True)
            after = subprocess.run(["git", "-C", str(destination), "status", "--porcelain", "--untracked-files=all"], check=True, capture_output=True, text=True).stdout
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("[quality-qa]", result.stdout)
            self.assertEqual(before, after)
            self.assertFalse((destination / ".agents/skills/quality-qa").exists())

    def test_same_version_unknown_changes_stop_even_in_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "Productivity-Skill"
            destination.mkdir()
            (destination / "README.md").write_text("Productivity-Skill\n")
            target = self.prepare_destination(destination)
            shutil.copytree(SOURCE / "quality-review", target / "quality-review")
            shutil.copytree(SOURCE / "quality-response", target / "quality-response")
            local_skill = target / "quality-review"
            with (local_skill / "SKILL.md").open("a") as stream:
                stream.write("\nlocal additional instruction\n")
            result = subprocess.run(["python3", str(SCRIPT), "--destination", str(destination), "--dry-run"], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertIn("同じVERSION", result.stderr)
            self.assertIn("local additional instruction", (local_skill / "SKILL.md").read_text())

    def test_destination_only_files_are_never_silently_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "Productivity-Skill"
            destination.mkdir()
            (destination / "README.md").write_text("Productivity-Skill\n")
            target = self.prepare_destination(destination)
            shutil.copytree(SOURCE / "quality-review", target / "quality-review")
            shutil.copytree(SOURCE / "quality-response", target / "quality-response")
            extra = target / "quality-review" / "local_feature.md"
            extra.write_text("preserve\n")
            result = subprocess.run(["python3", str(SCRIPT), "--destination", str(destination), "--dry-run"], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertIn("コピー元にない追加ファイル", result.stderr)
            self.assertEqual("preserve\n", extra.read_text())

    def test_dirty_destination_is_not_overridden_by_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "Productivity-Skill"
            destination.mkdir()
            (destination / "README.md").write_text("Productivity-Skill\n")
            target = self.prepare_destination(destination)
            shutil.copytree(SOURCE / "quality-review", target / "quality-review")
            shutil.copytree(SOURCE / "quality-response", target / "quality-response")
            result = subprocess.run(["python3", str(SCRIPT), "--destination", str(destination), "--force"], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertIn("未コミット変更", result.stderr)
            self.assertFalse((target / "quality-qa").exists())

    def test_version_upgrade_requires_package_specific_acknowledgement(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "Productivity-Skill"
            destination.mkdir()
            (destination / "README.md").write_text("Productivity-Skill\n")
            target = self.prepare_destination(destination)
            local_skill = target / "quality-qa"
            shutil.copytree(SOURCE / "quality-qa", local_skill)
            (local_skill / "VERSION").write_text("0.1.0\n")
            no_ack = subprocess.run(["python3", str(SCRIPT), "--destination", str(destination), "--dry-run"], capture_output=True, text=True)
            self.assertEqual(2, no_ack.returncode)
            self.assertIn("--replace-version quality-qa=0.1.0", no_ack.stderr)
            acknowledged = subprocess.run(["python3", str(SCRIPT), "--destination", str(destination), "--dry-run", "--replace-version", "quality-qa=0.1.0"], capture_output=True, text=True)
            self.assertEqual(0, acknowledged.returncode, acknowledged.stderr)
            self.assertEqual("0.1.0\n", (local_skill / "VERSION").read_text())


if __name__ == "__main__":
    unittest.main()
