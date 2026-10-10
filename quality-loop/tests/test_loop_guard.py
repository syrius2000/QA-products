from __future__ import annotations

import unittest

from qa_workflow.loop_guard import decide_stop


class LoopGuardTest(unittest.TestCase):
    def test_first_cycle_with_unresolved_findings_continues(self):
        decision = decide_stop([{"QA-F01"}])
        self.assertFalse(decision.stop)

    def test_same_finding_unresolved_in_two_consecutive_cycles_stops(self):
        decision = decide_stop([{"QA-F01"}, {"QA-F01", "QA-F02"}])
        self.assertTrue(decision.stop)
        self.assertIn("同一指摘", decision.reason)

    def test_different_findings_across_cycles_continue(self):
        decision = decide_stop([{"QA-F01"}, {"QA-F02"}])
        self.assertFalse(decision.stop)

    def test_finding_resolved_between_cycles_is_not_consecutive(self):
        decision = decide_stop([{"QA-F01"}, set()])
        self.assertFalse(decision.stop)

    def test_third_cycle_with_unresolved_findings_stops_at_cap(self):
        decision = decide_stop([{"QA-F01"}, {"QA-F02"}, {"QA-F03"}])
        self.assertTrue(decision.stop)
        self.assertIn("上限", decision.reason)

    def test_acknowledged_repetition_does_not_stop(self):
        decision = decide_stop([{"QA-F01"}, {"QA-F01"}], acknowledged=frozenset({"QA-F01"}))
        self.assertFalse(decision.stop)

    def test_repetition_of_an_unacknowledged_finding_still_stops(self):
        decision = decide_stop([{"QA-F01", "QA-F02"}, {"QA-F01", "QA-F02"}], acknowledged=frozenset({"QA-F01"}))
        self.assertTrue(decision.stop)
        self.assertIn("同一指摘", decision.reason)

    def test_acknowledgement_does_not_waive_the_cycle_cap(self):
        decision = decide_stop([{"QA-F01"}, {"QA-F02"}, {"QA-F01"}], acknowledged=frozenset({"QA-F01", "QA-F02"}))
        self.assertTrue(decision.stop)
        self.assertIn("上限", decision.reason)

    def test_fully_resolved_cycle_does_not_stop(self):
        decision = decide_stop([{"QA-F01"}, set()])
        self.assertFalse(decision.stop)


if __name__ == "__main__":
    unittest.main()
