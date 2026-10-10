from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from qa_workflow import cli
from qa_workflow.store import QAError


def run(argv: list[str]):
    return cli.execute(cli.parser().parse_args(argv))


class DispatchTest(unittest.TestCase):
    """Each subcommand must reach the matching Workflow method with its arguments mapped correctly."""

    def setUp(self):
        patcher = mock.patch.object(cli, "Workflow")
        self.workflow_class = patcher.start()
        self.addCleanup(patcher.stop)
        self.w = self.workflow_class.return_value

    def test_status_passes_the_request(self):
        run(["--root", "/r", "status", "--request", "QA-001"])
        self.w.status.assert_called_once_with("QA-001")

    def test_verify_passes_the_revision(self):
        run(["--root", "/r", "verify", "--request", "QA-001", "--revision", "3"])
        self.w.verify.assert_called_once_with("QA-001", revision=3)

    def test_finalize_maps_commit_message_and_paths(self):
        run(["--root", "/r", "finalize", "--request", "QA-001", "--commit", "abc", "--message", "m",
             "--approved-path", "p", "--revision", "3"])
        self.w.finalize.assert_called_once_with("QA-001", "abc", "m", ["p"], revision=3)

    def test_publish_maps_message_and_paths(self):
        run(["--root", "/r", "publish", "--request", "QA-001", "--message", "クラウドQAに出して",
             "--approved-path", "p", "--revision", "3"])
        self.w.publish.assert_called_once_with("QA-001", "クラウドQAに出して", ["p"], revision=3)

    def test_publish_correction_maps_message_and_paths(self):
        run(["--root", "/r", "publish-correction", "--request", "QA-001", "--message", "クラウドQAに出して",
             "--approved-path", "p", "--revision", "3"])
        self.w.publish_correction.assert_called_once_with("QA-001", "クラウドQAに出して", ["p"], revision=3)

    def test_handoff_passes_the_revision(self):
        run(["--root", "/r", "handoff", "--request", "QA-001", "--revision", "3"])
        self.w.handoff.assert_called_once_with("QA-001", revision=3)

    def test_acquire_branch_is_passed_with_no_body_or_pr(self):
        run(["--root", "/r", "acquire", "--request", "QA-001", "--branch", "b", "--revision", "3"])
        self.w.acquire.assert_called_once_with("QA-001", None, "b", None, revision=3)

    def test_acquire_body_is_passed_as_a_path(self):
        run(["--root", "/r", "acquire", "--request", "QA-001", "--body", "x.md", "--revision", "3"])
        self.w.acquire.assert_called_once_with("QA-001", Path("x.md"), None, None, revision=3)

    def test_confirm_content_maps_evidence_and_checker(self):
        run(["--root", "/r", "confirm-content", "--request", "QA-001", "--evidence", "ev", "--checker", "ch", "--revision", "3"])
        self.w.confirm_content.assert_called_once_with("QA-001", "ev", "ch", revision=3)

    def test_correction_maps_reason(self):
        run(["--root", "/r", "correction", "--request", "QA-001", "--reason", "不足", "--revision", "3"])
        self.w.correction.assert_called_once_with("QA-001", "不足", revision=3)

    def test_plan_reads_the_json_input_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "plan.json"
            source.write_text(json.dumps([{"id": "QA-F01"}]), encoding="utf-8")
            run(["--root", "/r", "plan", "--request", "QA-001", "--input", str(source), "--revision", "3"])
        self.w.plan.assert_called_once_with("QA-001", [{"id": "QA-F01"}], revision=3)

    def test_approve_maps_message_plan_hash_and_paths(self):
        run(["--root", "/r", "approve", "--request", "QA-001", "--message", "m", "--plan-hash", "h",
             "--approved-path", "p", "--revision", "3"])
        self.w.approve.assert_called_once_with("QA-001", "m", "h", ["p"], revision=3)

    def test_submit_maps_targets_evidence_and_method(self):
        run(["--root", "/r", "submit", "--request", "QA-001", "--target", "t", "--evidence", "ev",
             "--method", "方式", "--unverified", "u", "--revision", "3"])
        self.w.submit.assert_called_once_with("QA-001", ["t"], "ev", ["u"], "方式", revision=3)

    def test_requa_passes_audience_and_empty_options(self):
        run(["--root", "/r", "requa", "--request", "QA-001", "--audience", "cloud", "--revision", "3"])
        _, kwargs = self.w.requa.call_args
        self.assertEqual("cloud", self.w.requa.call_args.args[1])
        self.assertIsNone(kwargs["checks"])
        self.assertIsNone(kwargs["check_contract_approval"])
        self.assertEqual(3, kwargs["revision"])

    def test_assess_residual_maps_message_and_reason(self):
        run(["--root", "/r", "assess-residual", "--request", "QA-001", "--message", "m", "--reason", "r", "--revision", "3"])
        self.w.assess_residual.assert_called_once_with("QA-001", "m", "r", revision=3)

    def test_decide_maps_message_and_residual(self):
        run(["--root", "/r", "decide", "--request", "QA-001", "--message", "m", "--residual", "res", "--revision", "3"])
        self.w.decide.assert_called_once_with("QA-001", "m", "res", revision=3)

    def test_loop_maps_evidence_and_unverified_items(self):
        run(["--root", "/r", "loop", "--request", "QA-001", "--evidence", "ev", "--unverified", "u", "--revision", "3"])
        self.w.loop.assert_called_once_with("QA-001", "ev", ["u"], revision=3)

    def test_authorize_publish_maps_message(self):
        run(["--root", "/r", "authorize-publish", "--request", "QA-001", "--message", "クラウドQAに出して"])
        self.w.authorize_publish.assert_called_once_with("QA-001", "クラウドQAに出して", revision=None)

    def test_authorize_continue_maps_message(self):
        run(["--root", "/r", "authorize-continue", "--request", "QA-001", "--message", "続行する"])
        self.w.authorize_continue.assert_called_once_with("QA-001", "続行する", revision=None)

    def test_prepare_maps_the_request_fields(self):
        run(["--root", "/r", "prepare", "--purpose", "目的", "--criterion", "基準1", "--criterion", "基準2",
             "--target", "src/a.py", "--implementer", "Impl", "--author", "Auth", "--audience", "local",
             "--repository", "example/repo"])
        args = self.w.prepare.call_args.args
        self.assertEqual(("目的", ["基準1", "基準2"], ["src/a.py"], "Impl", "Auth", "local"), args[:6])
        self.assertEqual("example/repo", args[9])

    def test_prepare_refuses_the_retired_required_test_option(self):
        with self.assertRaisesRegex(QAError, "廃止予定"):
            run(["--root", "/r", "prepare", "--purpose", "目的", "--criterion", "基準", "--target", "src/a.py",
                 "--implementer", "Impl", "--author", "Auth", "--required-test", "pytest"])
        self.w.prepare.assert_not_called()

    def test_legacy_reads_the_old_artifacts(self):
        with mock.patch.object(cli, "read_legacy", return_value={"ok": True}) as legacy:
            result = run(["--root", "/r", "legacy", "--directory", "d", "--invite", "i.md"])
        legacy.assert_called_once_with(Path("d"), Path("i.md"))
        self.assertEqual({"ok": True}, result)

    def test_preflight_uses_the_read_only_status(self):
        with mock.patch.object(cli.gitops, "status_preflight", return_value={"clean": True}) as preflight:
            result = run(["--root", "/r", "preflight"])
        preflight.assert_called_once_with(Path("/r"))
        self.assertEqual({"clean": True}, result)
        self.workflow_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
