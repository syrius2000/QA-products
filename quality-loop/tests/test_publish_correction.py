from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from qa_workflow import gitops
from qa_workflow.store import QAError
from qa_workflow.workflow import Workflow

CLOUD = "クラウドQAに出して"


def run_git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


def setup_bare_remote(root: Path) -> tuple[Path, Path]:
    repository = root / "repo"
    remote = root / "remote.git"
    subprocess.run(["git", "init", "--bare", "-b", "master", str(remote)], check=True, capture_output=True)
    repository.mkdir()
    run_git(repository, "init", "-b", "master")
    run_git(repository, "config", "user.name", "QA Test")
    run_git(repository, "config", "user.email", "qa@example.invalid")
    run_git(repository, "remote", "add", "origin", str(remote))
    for path in [
        "quality-loop/skills/quality-qa/SKILL.md",
        "quality-loop/skills/quality-qa/references/reviewer_contract.md",
        "src/product.py",
    ]:
        target = repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("baseline\n")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "baseline")
    run_git(repository, "push", "-u", "origin", "master")
    run_git(repository, "remote", "set-head", "origin", "master")
    run_git(repository, "switch", "-c", "topic/qa")
    return repository, remote


class PublishCorrectionTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.repository, self.remote = setup_bare_remote(Path(self.directory.name))
        self.workflow = Workflow(self.repository)
        prepared = self.workflow.prepare(
            "対象製品をQAする", ["対象製品を読むこと"], ["src/product.py"],
            "Implementer", "Codex (GPT-6)", "cloud", repository="example/repo",
        )
        self.prepared = prepared
        broken = self.repository / "incomplete.md"
        broken.write_text("# broken\n")
        self.workflow.acquire(prepared["id"], body=broken)
        self.correction = self.workflow.correction(prepared["id"], "必須契約項目が不足しています")
        self.state = self.workflow.store.read(prepared["state_path"])
        self.invite = self.state["pending_correction"]["invite"]

    def tearDown(self):
        self.directory.cleanup()

    def test_correction_is_published_only_with_an_explicit_cloud_instruction(self):
        with self.assertRaisesRegex(QAError, "明示的な公開指示"):
            self.workflow.publish_correction(self.prepared["id"], "公開して", [self.invite])
        self.assertIsNone(gitops.remote_tip(self.repository, "topic/qa"))

    def test_only_the_correction_invite_may_be_published(self):
        with self.assertRaisesRegex(QAError, "訂正依頼だけ"):
            self.workflow.publish_correction(self.prepared["id"], CLOUD, [self.invite, "src/product.py"])
        self.assertIsNone(gitops.remote_tip(self.repository, "topic/qa"))

    def test_correction_invite_with_a_secret_is_not_published(self):
        path = self.repository / self.invite
        path.write_text(path.read_text() + "\napi_" + "token" + " = " + "'" + "real-value-1234" + "'\n")
        with self.assertRaisesRegex(QAError, "機密情報"):
            self.workflow.publish_correction(self.prepared["id"], CLOUD, [self.invite])
        self.assertIsNone(gitops.remote_tip(self.repository, "topic/qa"))

    def test_correction_is_committed_pushed_and_recorded(self):
        before = gitops.remote_tip(self.repository, "topic/qa")
        saved = self.workflow.publish_correction(self.prepared["id"], CLOUD, [self.invite])
        state = self.workflow.store.read(saved["state_path"])
        published = state["pending_correction"]["published"]
        self.assertEqual(published["tip"], gitops.remote_tip(self.repository, "topic/qa"))
        self.assertNotEqual(before, published["tip"])
        self.assertTrue(gitops.ancestor(self.repository, published["commit"], published["tip"]))
        self.assertIn(self.invite, state["published_paths"])
        self.assertIn(CLOUD, published["message"])


if __name__ == "__main__":
    unittest.main()
