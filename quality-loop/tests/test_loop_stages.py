from __future__ import annotations

import unittest

from qa_workflow.loop_stages import STAGES, run_stages, stage_status
from qa_workflow.store import QAError


class Recorder:
    def __init__(self):
        self.saved: list[tuple[dict, dict | None]] = []

    def save(self, done: dict, failed: dict | None = None) -> None:
        self.saved.append((dict(done), failed))


def actions(calls: list[str], fail_at: str | None = None) -> dict:
    def make(name: str):
        def run() -> dict:
            calls.append(name)
            if name == fail_at:
                raise QAError(f"{name}に失敗しました", "再実行してください")
            return {"stage": name}
        return run
    return {name: make(name) for name in STAGES}


class ResumeAfterFailureTest(unittest.TestCase):
    def test_retry_does_not_repeat_completed_stages(self):
        recorder = Recorder()
        calls: list[str] = []
        with self.assertRaises(QAError):
            run_stages({}, actions(calls, fail_at="finalize"), recorder.save)
        self.assertEqual(["commit", "submit", "requa-request", "finalize"], calls)

        retry_calls: list[str] = []
        done = recorder.saved[-1][0]
        run_stages(done, actions(retry_calls), recorder.save)
        self.assertEqual(["finalize", "publish"], retry_calls)

    def test_completed_stages_are_saved_before_failure(self):
        recorder = Recorder()
        with self.assertRaises(QAError):
            run_stages({}, actions([], fail_at="submit"), recorder.save)
        done, failed = recorder.saved[-1]
        self.assertEqual({"commit"}, set(done))
        self.assertEqual("submit", failed["stage"])


class StageStatusTest(unittest.TestCase):
    def test_status_reports_completed_failed_and_next_stage(self):
        recorder = Recorder()
        with self.assertRaises(QAError):
            run_stages({}, actions([], fail_at="requa-request"), recorder.save)
        done, _ = recorder.saved[-1]
        status = stage_status(done, failed={"stage": "requa-request", "reason": "再QA依頼に失敗しました"})
        self.assertEqual(["commit", "submit"], status["completed"])
        self.assertEqual("requa-request", status["failed"]["stage"])
        self.assertEqual("requa-request", status["next"])

    def test_status_without_failure_points_to_first_pending_stage(self):
        status = stage_status({}, failed=None)
        self.assertEqual([], status["completed"])
        self.assertIsNone(status["failed"])
        self.assertEqual("commit", status["next"])


if __name__ == "__main__":
    unittest.main()
