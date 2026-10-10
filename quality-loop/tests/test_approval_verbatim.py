from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from qa_workflow.prompt_log import verbatim_in_log


def write_log(path: Path, prompts: list[str]) -> None:
    lines = [json.dumps({"ts": "2026-10-10T00:00:00Z", "prompt": p}, ensure_ascii=False) for p in prompts]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class ApprovalVerbatimTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.log = Path(self.directory.name) / "qa-user-prompts.jsonl"

    def tearDown(self):
        self.directory.cleanup()

    def test_message_equal_to_logged_prompt_is_accepted(self):
        write_log(self.log, ["この計画で修正して"])
        self.assertTrue(verbatim_in_log(self.log, "この計画で修正して"))

    def test_message_contained_in_logged_prompt_is_accepted(self):
        write_log(self.log, ["確認しました。この計画で修正して。よろしく"])
        self.assertTrue(verbatim_in_log(self.log, "この計画で修正して"))

    def test_paraphrase_by_assistant_is_rejected(self):
        write_log(self.log, ["この計画で修正して"])
        self.assertFalse(verbatim_in_log(self.log, "計画どおりに修正することを承認します"))

    def test_missing_log_is_rejected(self):
        self.assertFalse(verbatim_in_log(self.log, "この計画で修正して"))

    def test_empty_message_is_rejected(self):
        write_log(self.log, ["この計画で修正して"])
        self.assertFalse(verbatim_in_log(self.log, "   "))

    def test_malformed_lines_are_ignored(self):
        self.log.write_text("not json\n" + json.dumps({"prompt": "この計画で修正して"}, ensure_ascii=False) + "\n", encoding="utf-8")
        self.assertTrue(verbatim_in_log(self.log, "この計画で修正して"))


if __name__ == "__main__":
    unittest.main()
