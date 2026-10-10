from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from qa_workflow.cli import main, parser


def run_git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


def make_repository(root: Path) -> Path:
    repository = root / "repo"
    repository.mkdir()
    run_git(repository, "init", "-b", "master")
    run_git(repository, "config", "user.name", "QA Test")
    run_git(repository, "config", "user.email", "qa@example.invalid")
    (repository / "src").mkdir()
    (repository / "src/product.py").write_text("baseline\n")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "-m", "baseline")
    run_git(repository, "switch", "-c", "topic/qa")
    return repository


def call(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(argv)
    return code, out.getvalue()


class CliOutcomeTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.repository = make_repository(Path(self.directory.name))

    def tearDown(self):
        self.directory.cleanup()

    def test_every_documented_operation_is_a_subcommand(self):
        operations = set(parser()._subparsers._group_actions[0].choices)
        for name in ["preflight", "prepare", "status", "verify", "finalize", "publish", "handoff", "acquire",
                     "confirm-content", "correction", "publish-correction", "plan", "approve", "submit", "requa",
                     "assess-residual", "decide", "loop", "authorize-publish", "authorize-continue", "legacy"]:
            with self.subTest(operation=name):
                self.assertIn(name, operations)

    def test_unknown_operation_is_rejected_by_the_parser(self):
        with self.assertRaises(SystemExit):
            parser().parse_args(["no-such-operation"])

    def test_preflight_on_a_clean_branch_without_origin_is_not_safe_to_implement(self):
        code, out = call(["--root", str(self.repository), "--json", "preflight"])
        self.assertEqual(0, code)
        result = json.loads(out)
        self.assertTrue(result["clean"])
        self.assertFalse(result["safe_to_implement"])
        self.assertEqual([], result["remotes"])

    def test_status_without_any_request_returns_an_error_and_exit_code_2(self):
        code, out = call(["--root", str(self.repository), "--json", "status"])
        self.assertEqual(2, code)
        self.assertIn("error", json.loads(out))

    def test_json_error_carries_the_next_step_for_the_user(self):
        _, out = call(["--root", str(self.repository), "--json", "status"])
        next_step = json.loads(out)["next"]
        self.assertEqual("ユーザーまたはローカル担当", next_step["担当"])
        self.assertIsNone(next_step["依頼文"])

    def test_text_output_prints_the_state_and_next_action(self):
        code, out = call(["--root", str(self.repository), "prepare",
                          "--purpose", "対象製品をQAする", "--criterion", "対象製品を読むこと",
                          "--target", "src/product.py", "--implementer", "Implementer",
                          "--author", "Codex (GPT-6)", "--audience", "cloud", "--repository", "example/repo"])
        self.assertEqual(0, code)
        self.assertIn("依頼 QA-001", out)
        self.assertIn("サイクル 1", out)
        self.assertIn("担当:", out)
        self.assertIn("必要入力:", out)

    def test_prepare_with_an_exclusion_records_the_reason(self):
        (self.repository / "src/extra.py").write_text("extra\n")
        run_git(self.repository, "add", "src/extra.py")
        run_git(self.repository, "commit", "-m", "extra")
        code, out = call(["--root", str(self.repository), "--json", "prepare",
                          "--purpose", "対象製品をQAする", "--criterion", "対象製品を読むこと",
                          "--target", "src/product.py", "--implementer", "Implementer",
                          "--author", "Codex (GPT-6)", "--audience", "local", "--repository", "example/repo",
                          "--exclude", "src/extra.py=対象外の補助ファイル"])
        self.assertEqual(0, code, out)
        self.assertEqual("QA-001", json.loads(out)["id"])


if __name__ == "__main__":
    unittest.main()
