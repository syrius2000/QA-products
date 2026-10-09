from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from qa_workflow.publish_guard import assert_publishable, assert_reachable_from_origin
from qa_workflow.store import QAError


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


class PublishGuardTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        git(self.root, "init", "-b", "topic/qa")
        git(self.root, "config", "user.name", "Test User")
        git(self.root, "config", "user.email", "test@example.com")
        (self.root / "src").mkdir()
        (self.root / "src/product.py").write_text("print('ok')\n")
        git(self.root, "add", "src")
        git(self.root, "commit", "-m", "base")
        self.base = git(self.root, "rev-parse", "HEAD")

    def tearDown(self):
        self.directory.cleanup()

    def test_personal_local_path_blocks_publication(self):
        (self.root / "src/product.py").write_text("path = '/Users/someone/private/notes'\n")
        with self.assertRaisesRegex(QAError, "個人ローカルパス|機密情報"):
            assert_publishable(self.root, ["src/product.py"])

    def test_clean_content_is_publishable(self):
        assert_publishable(self.root, ["src/product.py"])

    def test_commit_not_on_origin_blocks_re_qa_request(self):
        git(self.root, "update-ref", "refs/remotes/origin/topic/qa", self.base)
        (self.root / "src/product.py").write_text("print('fixed')\n")
        git(self.root, "commit", "-am", "fix")
        new_sha = git(self.root, "rev-parse", "HEAD")
        with self.assertRaisesRegex(QAError, "祖先"):
            assert_reachable_from_origin(self.root, "topic/qa", [new_sha])

    def test_commit_on_origin_is_accepted(self):
        git(self.root, "update-ref", "refs/remotes/origin/topic/qa", self.base)
        assert_reachable_from_origin(self.root, "topic/qa", [self.base])


if __name__ == "__main__":
    unittest.main()
