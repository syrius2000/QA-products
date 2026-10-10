from __future__ import annotations

import unittest

from qa_workflow.minor_change import ApprovedScope, ChangeSet, judge_minor_change

CONTRACT = "a" * 64
CONTRACT_REASON = "完了条件・受入基準・確認方法の変更"


def approved() -> ApprovedScope:
    return ApprovedScope(paths=frozenset({"quality-loop/skills/quality-qa/SKILL.md", "quality-loop/qa_workflow/cli.py"}), contract_hash=CONTRACT)


def change(**overrides) -> ChangeSet:
    values = {
        "paths": frozenset({"quality-loop/skills/quality-qa/SKILL.md"}),
        "added_paths": frozenset(),
        "contract_hash": CONTRACT,
    }
    values.update(overrides)
    return ChangeSet(**values)


class MinorChangeJudgementTest(unittest.TestCase):
    def test_change_inside_approved_scope_is_minor_without_outside_paths(self):
        decision = judge_minor_change(approved(), change())
        self.assertTrue(decision.minor)
        self.assertEqual((), decision.reasons)
        self.assertEqual((), decision.outside_paths)

    def test_path_outside_approved_scope_is_minor_and_recorded(self):
        decision = judge_minor_change(approved(), change(paths=frozenset({"quality-loop/README.md"})))
        self.assertTrue(decision.minor)
        self.assertEqual((), decision.reasons)
        self.assertEqual(("quality-loop/README.md",), decision.outside_paths)

    def test_new_path_is_minor_and_recorded(self):
        decision = judge_minor_change(
            approved(),
            change(added_paths=frozenset({"quality-loop/skills/quality-qa/NEW.md"})),
        )
        self.assertTrue(decision.minor)
        self.assertEqual(("quality-loop/skills/quality-qa/NEW.md",), decision.outside_paths)

    def test_changed_contract_is_not_minor(self):
        decision = judge_minor_change(approved(), change(contract_hash="b" * 64))
        self.assertFalse(decision.minor)
        self.assertEqual((CONTRACT_REASON,), decision.reasons)

    def test_contract_change_outside_scope_reports_only_the_contract_reason(self):
        decision = judge_minor_change(
            approved(),
            change(paths=frozenset({"quality-loop/README.md"}), contract_hash="b" * 64),
        )
        self.assertFalse(decision.minor)
        self.assertEqual((CONTRACT_REASON,), decision.reasons)
        self.assertEqual(("quality-loop/README.md",), decision.outside_paths)


if __name__ == "__main__":
    unittest.main()
