from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from qa_workflow import gitops
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
        (self.root / "src/product.py").write_text("path = '" + "/" + "Users/someone/private/notes'\n")
        with self.assertRaisesRegex(QAError, "個人ローカルパス|機密情報"):
            assert_publishable(self.root, ["src/product.py"])

    def test_clean_content_is_publishable(self):
        assert_publishable(self.root, ["src/product.py"])

    def test_outgoing_scan_flags_a_secret_in_a_committed_blob(self):
        (self.root / "src/product.py").write_text("api_" + "token" + " = " + "'" + "real-value-1234" + "'\n")
        git(self.root, "commit", "-am", "add secret")
        findings = gitops.outgoing_findings(self.root, self.base, "HEAD")
        self.assertEqual(["src/product.py:secret-like-assignment"], findings)

    def test_outgoing_scan_flags_a_personal_path_in_a_committed_blob(self):
        (self.root / "src/product.py").write_text("path = '" + "/" + "Users/someone/private'\n")
        git(self.root, "commit", "-am", "add path")
        self.assertEqual(["src/product.py:personal-local-path"], gitops.outgoing_findings(self.root, self.base, "HEAD"))

    def test_outgoing_scan_reads_commits_not_the_working_tree(self):
        git(self.root, "commit", "--allow-empty", "-m", "empty")
        (self.root / "src/product.py").write_text("api_" + "token" + " = " + "'" + "real-value-1234" + "'\n")
        self.assertEqual([], gitops.outgoing_findings(self.root, self.base, "HEAD"))

    def test_outgoing_scan_ignores_deleted_files(self):
        (self.root / "src/product.py").unlink()
        git(self.root, "commit", "-am", "delete")
        self.assertEqual([], gitops.outgoing_findings(self.root, self.base, "HEAD"))

    def test_the_scanner_source_does_not_flag_itself(self):
        runtime = Path(gitops.__file__).parent.parent / "skills/quality-qa/runtime/qa_workflow/gitops.py"
        for path in (Path(gitops.__file__), runtime):
            with self.subTest(path=str(path)):
                self.assertEqual([], gitops._scan_text(path.name, path.read_text(encoding="utf-8")))

    def test_outgoing_scan_flags_a_secret_added_and_removed_in_later_commits(self):
        safe = (self.root / "src/product.py").read_text()
        (self.root / "src/product.py").write_text("api_" + "token" + " = " + "'" + "real-value-1234" + "'\n")
        git(self.root, "commit", "-am", "add secret")
        (self.root / "src/product.py").write_text(safe)
        git(self.root, "commit", "-am", "restore")
        self.assertEqual("", git(self.root, "diff", "--name-only", self.base, "HEAD"))
        self.assertEqual(["src/product.py:secret-like-assignment"], gitops.outgoing_findings(self.root, self.base, "HEAD"))

    def test_outgoing_scan_reports_each_finding_once(self):
        leaked = "api_" + "token" + " = " + "'" + "real-value-1234" + "'\n"
        safe = (self.root / "src/product.py").read_text()
        for message, content in (("add", leaked), ("restore", safe), ("add again", leaked)):
            (self.root / "src/product.py").write_text(content)
            git(self.root, "commit", "-am", message)
        self.assertEqual(["src/product.py:secret-like-assignment"], gitops.outgoing_findings(self.root, self.base, "HEAD"))

    def test_outgoing_scan_ignores_a_secret_that_only_exists_in_the_base(self):
        (self.root / "src/other.py").write_text("print('ok')\n")
        git(self.root, "add", "src/other.py")
        git(self.root, "commit", "-m", "other")
        self.assertEqual([], gitops.outgoing_findings(self.root, self.base, "HEAD"))

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


class GuardedPushTest(unittest.TestCase):
    LEAK = "api_" + "token" + " = " + "'" + "real-value-1234" + "'\n"

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        base = Path(self.directory.name)
        self.remote = base / "remote.git"
        subprocess.run(["git", "init", "--bare", "-b", "master", str(self.remote)], check=True, capture_output=True)
        self.root = base / "repo"
        self.root.mkdir()
        git(self.root, "init", "-b", "topic/qa")
        git(self.root, "config", "user.name", "Test User")
        git(self.root, "config", "user.email", "test@example.com")
        git(self.root, "remote", "add", "origin", str(self.remote))
        (self.root / "src").mkdir()
        (self.root / "src/product.py").write_text("print('ok')\n")
        git(self.root, "add", "src")
        git(self.root, "commit", "-m", "base")
        self.base = git(self.root, "rev-parse", "HEAD")
        self.state = {"branch": "topic/qa", "initial_baseline": self.base, "reviewed": self.base}

    def tearDown(self):
        self.directory.cleanup()

    def add_then_remove_a_leak(self):
        safe = (self.root / "src/product.py").read_text()
        (self.root / "src/product.py").write_text(self.LEAK)
        git(self.root, "commit", "-am", "temporary leak")
        (self.root / "src/product.py").write_text(safe)
        git(self.root, "commit", "-am", "restore")

    def test_guarded_push_refuses_a_leak_added_and_removed_in_the_history(self):
        self.add_then_remove_a_leak()
        with self.assertRaisesRegex(QAError, "機密情報"):
            gitops.guarded_push(self.root, self.state)
        self.assertIsNone(gitops.remote_tip(self.root, "topic/qa"))

    def test_guarded_push_sends_a_clean_history(self):
        (self.root / "src/product.py").write_text("print('fixed')\n")
        git(self.root, "commit", "-am", "fix")
        gitops.guarded_push(self.root, self.state)
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), gitops.remote_tip(self.root, "topic/qa"))

    def test_publish_push_goes_through_the_guard(self):
        self.add_then_remove_a_leak()
        head = git(self.root, "rev-parse", "HEAD")
        with self.assertRaisesRegex(QAError, "機密情報"):
            gitops.push(self.root, self.state, head)
        self.assertIsNone(gitops.remote_tip(self.root, "topic/qa"))

    def test_the_guard_is_the_only_place_that_runs_git_push(self):
        source_dir = Path(gitops.__file__).parent
        callers = [path.name for path in sorted(source_dir.glob("*.py")) if '"push", "origin"' in path.read_text(encoding="utf-8")]
        self.assertEqual(["gitops.py"], callers)


if __name__ == "__main__":
    unittest.main()
