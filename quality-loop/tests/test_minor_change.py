from __future__ import annotations

import unittest

from qa_workflow.minor_change import ApprovedScope, ChangeSet, judge_minor_change

LINE_LIMIT = 50
CONTRACT = "a" * 64


def approved() -> ApprovedScope:
    return ApprovedScope(paths=frozenset({"quality-loop/skills/quality-qa/SKILL.md", "quality-loop/qa_workflow/cli.py"}), contract_hash=CONTRACT)


def change(**overrides) -> ChangeSet:
    values = {
        "paths": frozenset({"quality-loop/skills/quality-qa/SKILL.md"}),
        "added_paths": frozenset(),
        "contract_hash": CONTRACT,
        "changed_lines": 10,
    }
    values.update(overrides)
    return ChangeSet(**values)


class MinorChangeJudgementTest(unittest.TestCase):
    def test_all_rules_satisfied_is_minor(self):
        decision = judge_minor_change(approved(), change(), LINE_LIMIT)
        self.assertTrue(decision.minor)

    def test_path_outside_approved_scope_is_not_minor(self):
        decision = judge_minor_change(approved(), change(paths=frozenset({"quality-loop/README.md"})), LINE_LIMIT)
        self.assertFalse(decision.minor)

    def test_new_path_is_not_minor(self):
        decision = judge_minor_change(
            approved(),
            change(paths=frozenset({"quality-loop/skills/quality-qa/SKILL.md"}), added_paths=frozenset({"quality-loop/skills/quality-qa/NEW.md"})),
            LINE_LIMIT,
        )
        self.assertFalse(decision.minor)

    def test_changed_contract_is_not_minor(self):
        decision = judge_minor_change(approved(), change(contract_hash="b" * 64), LINE_LIMIT)
        self.assertFalse(decision.minor)

    def test_line_count_over_limit_is_not_minor(self):
        decision = judge_minor_change(approved(), change(changed_lines=LINE_LIMIT + 1), LINE_LIMIT)
        self.assertFalse(decision.minor)

    def test_line_count_at_limit_is_minor(self):
        decision = judge_minor_change(approved(), change(changed_lines=LINE_LIMIT), LINE_LIMIT)
        self.assertTrue(decision.minor)

    def test_stop_reasons_are_recorded_for_each_violated_rule(self):
        decision = judge_minor_change(
            approved(),
            change(paths=frozenset({"quality-loop/README.md"}), contract_hash="b" * 64, changed_lines=LINE_LIMIT + 1),
            LINE_LIMIT,
        )
        self.assertFalse(decision.minor)
        self.assertEqual(
            decision.reasons,
            ("承認済み対象パス外の変更", "完了条件・受入基準・確認方法の変更", "変更行数が上限を超える"),
        )

    def test_minor_decision_has_no_reasons(self):
        decision = judge_minor_change(approved(), change(), LINE_LIMIT)
        self.assertEqual(decision.reasons, ())


if __name__ == "__main__":
    unittest.main()
