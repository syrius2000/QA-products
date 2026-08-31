from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from quality_loop.errors import QualityLoopError
from quality_loop.observation import (
    compute_file_manifest,
    detect_manifest_changes,
    observe_git_changes,
    validate_change_observation,
)


class ObservationTest(unittest.TestCase):
    def test_compute_file_manifest_and_detect_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            f1 = dir_path / "file1.txt"
            f2 = dir_path / "file2.txt"
            f1.write_text("v1", encoding="utf-8")
            f2.write_text("v1", encoding="utf-8")

            scope = [str(f1), str(f2)]
            before_manifest = compute_file_manifest(scope)

            # Modify f1, keep f2
            f1.write_text("v2", encoding="utf-8")
            after_manifest = compute_file_manifest(scope)

            changed, added, removed = detect_manifest_changes(before_manifest, after_manifest)
            self.assertEqual([str(f1)], changed)
            self.assertEqual([], added)
            self.assertEqual([], removed)

    def test_observe_git_changes_detects_status_in_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = Path(temp_dir)
            # Initialize temporary git repo
            subprocess.run(["git", "init"], cwd=str(repo_dir), capture_output=True, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo_dir), check=True)
            subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=str(repo_dir), check=True)

            tracked = repo_dir / "tracked.txt"
            tracked.write_text("initial\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=str(repo_dir), check=True)
            subprocess.run(["git", "commit", "-m", "initial commit"], cwd=str(repo_dir), capture_output=True, check=True)

            # 1. Modify tracked file
            tracked.write_text("modified\n", encoding="utf-8")

            # 2. Add untracked file
            untracked = repo_dir / "untracked.txt"
            untracked.write_text("new\n", encoding="utf-8")

            observation = observe_git_changes(repo_dir, "HEAD")
            self.assertIn("tracked.txt", observation["observed_changed_targets"])
            self.assertIn("untracked.txt", observation["observed_changed_targets"])
            self.assertEqual([], observation["deleted_targets"])

    def test_observe_git_changes_fails_gracefully_when_not_git_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            non_git = Path(temp_dir)
            with self.assertRaises(QualityLoopError) as ctx:
                observe_git_changes(non_git, "HEAD")
            self.assertIn(ctx.exception.error_code, {"git-observation-failed", "git-not-available"})

    def test_validate_change_observation_detects_undeclared_changes(self) -> None:
        observation = {
            "method": "finite-manifest",
            "scope": ["src/a.py", "src/b.py"],
            "before_evidence_id": "EV-BEFORE",
            "after_evidence_id": "EV-AFTER",
            "observed_changed_targets": ["src/a.py", "src/b.py"],
            "limitations": [],
        }

        declared = {"src/a.py"}
        allowed = {"src/a.py", "src/b.py"}
        available_evidence_ids = {"EV-BEFORE", "EV-AFTER"}

        with self.assertRaises(QualityLoopError) as ctx:
            validate_change_observation(
                observation=observation,
                declared_changed_targets=declared,
                allowed_targets=allowed,
                available_evidence_ids=available_evidence_ids,
            )
        self.assertEqual("undeclared-change-detected", ctx.exception.error_code)

    def test_validate_change_observation_detects_unauthorized_changes(self) -> None:
        observation = {
            "method": "finite-manifest",
            "scope": ["src/a.py", "src/secret.py"],
            "before_evidence_id": "EV-BEFORE",
            "after_evidence_id": "EV-AFTER",
            "observed_changed_targets": ["src/a.py", "src/secret.py"],
            "limitations": [],
        }

        declared = {"src/a.py", "src/secret.py"}
        allowed = {"src/a.py"}
        available_evidence_ids = {"EV-BEFORE", "EV-AFTER"}

        with self.assertRaises(QualityLoopError) as ctx:
            validate_change_observation(
                observation=observation,
                declared_changed_targets=declared,
                allowed_targets=allowed,
                available_evidence_ids=available_evidence_ids,
            )
        self.assertEqual("unauthorized-change-detected", ctx.exception.error_code)


if __name__ == "__main__":
    unittest.main()
