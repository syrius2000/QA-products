from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from qa_workflow.repair_commit import COMMIT_PHRASE, commit_approved_paths
from qa_workflow.store import QAError


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


def make_repository(root: Path) -> None:
    git(root, "init", "-b", "topic/qa")
    git(root, "config", "user.name", "Test User")
    git(root, "config", "user.email", "test@example.com")
    (root / "src").mkdir()
    (root / "src/product.py").write_text("before\n")
    (root / "src/other.py").write_text("before\n")
    git(root, "add", "src")
    git(root, "commit", "-m", "base")


class RepairCommitTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        make_repository(self.root)

    def tearDown(self):
        self.directory.cleanup()

    def test_commit_is_refused_without_commit_phrase_in_approval(self):
        (self.root / "src/product.py").write_text("after\n")
        head_before = git(self.root, "rev-parse", "HEAD")
        with self.assertRaisesRegex(QAError, "修正後のcommitの範囲"):
            commit_approved_paths(self.root, ["src/product.py"], "Yip: fix product", "この計画で修正して")
        self.assertEqual(head_before, git(self.root, "rev-parse", "HEAD"))

    def test_only_approved_paths_are_committed(self):
        (self.root / "src/product.py").write_text("after\n")
        (self.root / "src/other.py").write_text("unrelated change\n")
        (self.root / "notes.txt").write_text("untracked\n")
        sha = commit_approved_paths(self.root, ["src/product.py"], "Yip: fix product", f"この計画で修正して。{COMMIT_PHRASE}")
        self.assertEqual(sha, git(self.root, "rev-parse", "HEAD"))
        self.assertEqual(["src/product.py"], git(self.root, "show", "--name-only", "--format=", "HEAD").splitlines())
        self.assertIn("src/other.py", git(self.root, "status", "--porcelain"))
        self.assertIn("notes.txt", git(self.root, "status", "--porcelain"))

    def test_previously_staged_unrelated_change_is_not_committed(self):
        (self.root / "src/product.py").write_text("after\n")
        (self.root / "src/other.py").write_text("staged by someone else\n")
        git(self.root, "add", "src/other.py")
        commit_approved_paths(self.root, ["src/product.py"], "Yip: fix product", f"この計画で修正して。{COMMIT_PHRASE}")
        self.assertEqual(["src/product.py"], git(self.root, "show", "--name-only", "--format=", "HEAD").splitlines())
        self.assertIn("src/other.py", git(self.root, "diff", "--cached", "--name-only"))

    def test_same_path_staged_by_someone_else_is_not_overwritten(self):
        (self.root / "src/product.py").write_text("someone else staged\n")
        git(self.root, "add", "src/product.py")
        staged_before = git(self.root, "ls-files", "-s", "src/product.py")
        head_before = git(self.root, "rev-parse", "HEAD")
        (self.root / "src/product.py").write_text("approved fix\n")
        with self.assertRaisesRegex(QAError, "承認パスに他者のステージ済み変更"):
            commit_approved_paths(self.root, ["src/product.py"], "Yip: fix product", f"この計画で修正して。{COMMIT_PHRASE}")
        self.assertEqual(head_before, git(self.root, "rev-parse", "HEAD"))
        self.assertEqual(staged_before, git(self.root, "ls-files", "-s", "src/product.py"))


if __name__ == "__main__":
    unittest.main()
