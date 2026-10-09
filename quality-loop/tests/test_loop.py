from __future__ import annotations

import unittest

from qa_workflow.loop import CLOUD_PHRASE, run_loop
from qa_workflow.loop_stages import STAGES
from qa_workflow.minor_change import MinorDecision
from qa_workflow.repair_commit import COMMIT_PHRASE

BOTH = f"この計画で修正して。{COMMIT_PHRASE}。{CLOUD_PHRASE}"
COMMIT_ONLY = f"この計画で修正して。{COMMIT_PHRASE}"


class Harness:
    def __init__(self, fail_at: str | None = None):
        self.calls: list[str] = []
        self.saved: list[dict] = []
        self.fail_at = fail_at

    def actions(self) -> dict:
        from qa_workflow.store import QAError

        def make(name):
            def run():
                self.calls.append(name)
                if name == self.fail_at:
                    raise QAError(f"{name}に失敗しました", "再実行してください")
                return {"stage": name}
            return run

        return {name: make(name) for name in STAGES}

    def save(self, done, failed=None):
        self.saved.append(dict(done))


class LoopTest(unittest.TestCase):
    def test_before_approval_loop_presents_plan_and_runs_nothing(self):
        harness = Harness()
        result = run_loop("planned", BOTH, {}, harness.actions(), harness.save, [])
        self.assertEqual("waiting_approval", result.status)
        self.assertEqual([], harness.calls)

    def test_approval_with_commit_and_cloud_runs_through_re_qa_request(self):
        harness = Harness()
        result = run_loop("approved", BOTH, {}, harness.actions(), harness.save, [])
        self.assertEqual("completed", result.status)
        self.assertEqual(["commit", "submit", "push", "ancestry", "requa-request", "finalize", "publish"], harness.calls)

    def test_approval_without_cloud_instruction_stops_before_publish(self):
        harness = Harness()
        result = run_loop("approved", COMMIT_ONLY, {}, harness.actions(), harness.save, [])
        self.assertEqual("stopped", result.status)
        self.assertIn(CLOUD_PHRASE, result.reason)
        self.assertEqual(["commit", "submit"], harness.calls)

    def test_approval_without_commit_phrase_runs_nothing(self):
        harness = Harness()
        result = run_loop("approved", f"この計画で修正して。{CLOUD_PHRASE}", {}, harness.actions(), harness.save, [])
        self.assertEqual("stopped", result.status)
        self.assertIn(COMMIT_PHRASE, result.reason)
        self.assertEqual([], harness.calls)

    def test_repeated_unresolved_finding_stops_before_any_stage(self):
        harness = Harness()
        result = run_loop("approved", BOTH, {}, harness.actions(), harness.save, [{"QA-F01"}, {"QA-F01"}])
        self.assertEqual("stopped", result.status)
        self.assertIn("同一指摘", result.reason)
        self.assertEqual([], harness.calls)

    def test_out_of_scope_change_stops_before_any_stage(self):
        harness = Harness()
        minor = MinorDecision(minor=False, reasons=("完了条件・受入基準・確認方法の変更",))
        result = run_loop("approved", BOTH, {}, harness.actions(), harness.save, [], minor=minor)
        self.assertEqual("stopped", result.status)
        self.assertIn("完了条件・受入基準・確認方法の変更", result.reason)
        self.assertEqual([], harness.calls)

    def test_acknowledged_repetition_lets_the_loop_run(self):
        harness = Harness()
        result = run_loop("approved", BOTH, {}, harness.actions(), harness.save, [{"QA-F01"}, {"QA-F01"}], acknowledged=frozenset({"QA-F01"}))
        self.assertEqual("completed", result.status)

    def test_unacknowledged_repetition_still_stops_before_any_stage(self):
        harness = Harness()
        result = run_loop("approved", BOTH, {}, harness.actions(), harness.save, [{"QA-F01"}, {"QA-F01"}], acknowledged=frozenset({"QA-F02"}))
        self.assertEqual("stopped", result.status)
        self.assertEqual([], harness.calls)

    def test_failed_stage_is_reported_and_completed_stages_are_kept(self):
        harness = Harness(fail_at="finalize")
        result = run_loop("approved", BOTH, {}, harness.actions(), harness.save, [])
        self.assertEqual("failed", result.status)
        self.assertEqual(sorted(["commit", "submit", "push", "ancestry", "requa-request"]), sorted(result.done))

    def test_loop_never_records_a_verdict_of_its_own_fix(self):
        harness = Harness()
        result = run_loop("approved", BOTH, {}, harness.actions(), harness.save, [])
        self.assertNotIn("review", STAGES)
        self.assertFalse(hasattr(result, "verdict"))
        self.assertTrue(set(harness.calls) <= set(["commit", "submit", "push", "ancestry", "requa-request", "finalize", "publish"]))


if __name__ == "__main__":
    unittest.main()
