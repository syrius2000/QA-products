import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync_productivity_skills.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_productivity_skills", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DistributionToolsTest(unittest.TestCase):
    @staticmethod
    def initialize_target(path: Path) -> None:
        subprocess.run(["git", "init", "-q", str(path)], check=True)
        subprocess.run(
            ["git", "-C", str(path), "remote", "add", "origin", "https://github.com/syrius2000/Productivity-Skill.git"],
            check=True,
        )
        (path / "README.md").write_text("# Productivity-Skill\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(path), "add", "README.md"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(path),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-qm",
                "initial",
            ],
            check=True,
        )

    def test_dry_run_does_not_create_target_directories(self):
        module = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "Productivity-Skill"
            target.mkdir()
            self.initialize_target(target)
            result = module.main(["--destination", str(target), "--dry-run"])
            self.assertEqual(result, 0)
            self.assertFalse((target / ".agents").exists())

    def test_dirty_target_is_rejected_without_force(self):
        module = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "Productivity-Skill"
            target.mkdir()
            self.initialize_target(target)
            (target / "local-work.txt").write_text("keep\n", encoding="utf-8")
            result = module.main(["--destination", str(target)])
            self.assertEqual(result, 2)
            self.assertFalse((target / ".agents").exists())

    def test_clean_target_can_receive_both_skills(self):
        module = load_sync_module()
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "Productivity-Skill"
            target.mkdir()
            self.initialize_target(target)
            record = Path(temporary) / "sync-record.md"
            result = module.main(
                ["--destination", str(target), "--record", str(record), "--tag", "v1.4.0"]
            )
            self.assertEqual(result, 0)
            for skill_name in module.SKILL_NAMES:
                skill = target / ".agents" / "skills" / skill_name
                self.assertTrue((skill / "SKILL.md").is_file())
                self.assertTrue((skill / "VERSION").is_file())
            self.assertIn("tree SHA-256", record.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
