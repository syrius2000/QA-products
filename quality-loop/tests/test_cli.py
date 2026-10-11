from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_quality_loop import complete_intake


class CliTest(unittest.TestCase):
    def test_create_case_and_status_return_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            subprocess.run(["git", "init", "-q", temp_dir], check=True)
            input_path = Path(temp_dir) / "intake.json"
            input_path.write_text(
                json.dumps(complete_intake(), ensure_ascii=False), encoding="utf-8"
            )
            created = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    "-B",
                    "-m",
                    "quality_loop.cli",
                    "--case-root",
                    temp_dir,
                    "create-case",
                    "--input",
                    str(input_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, created.returncode, created.stderr)
            created_result = json.loads(created.stdout)
            self.assertEqual("review", created_result["next_action"])
            case_path = Path(temp_dir) / "QMS-0001" / "case.json"
            before = case_path.read_bytes()
            git_before = subprocess.run(
                ["git", "-C", temp_dir, "status", "--porcelain=v1", "--untracked-files=all"],
                check=True, capture_output=True, text=True,
            ).stdout

            status = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    "-B",
                    "-m",
                    "quality_loop.cli",
                    "--case-root",
                    temp_dir,
                    "status",
                    "--case-id",
                    "QMS-0001",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, status.returncode, status.stderr)
            status_result = json.loads(status.stdout)
            self.assertEqual(1, status_result["case_revision"])
            self.assertFalse(status_result["state_changed"])
            self.assertEqual("reviewer", status_result["handoff"]["next_role"])
            self.assertEqual("review", status_result["handoff"]["next_action"])

            status_en_json = subprocess.run(
                [
                    sys.executable, "-S", "-B", "-m", "quality_loop.cli",
                    "--case-root", temp_dir, "status", "--case-id", "QMS-0001", "--lang", "en",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, status_en_json.returncode, status_en_json.stderr)
            self.assertEqual(status_result, json.loads(status_en_json.stdout))

            status_text = subprocess.run(
                [
                    sys.executable, "-S", "-B", "-m", "quality_loop.cli",
                    "--case-root", temp_dir, "status", "--case-id", "QMS-0001", "--format", "text",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, status_text.returncode, status_text.stderr)
            self.assertIn("工程: QA・確認", status_text.stdout)
            self.assertIn("評価対象版（baseline.target_revision）: r1", status_text.stdout)
            self.assertIn("サイクル: 0/3", status_text.stdout)
            self.assertIn("次の担当: レビュー担当（reviewer）", status_text.stdout)
            self.assertIn("未解決Finding: 0件", status_text.stdout)
            self.assertEqual(before, case_path.read_bytes())

            status_text_en = subprocess.run(
                [
                    sys.executable, "-S", "-B", "-m", "quality_loop.cli",
                    "--case-root", temp_dir, "status", "--case-id", "QMS-0001", "--format", "text", "--lang", "en",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, status_text_en.returncode, status_text_en.stderr)
            self.assertIn("state reviewer-action", status_text_en.stdout)
            self.assertIn("Next role: reviewer", status_text_en.stdout)
            self.assertEqual(before, case_path.read_bytes())

            incompatible = subprocess.run(
                [
                    sys.executable, "-S", "-B", "-m", "quality_loop.cli",
                    "--case-root", temp_dir, "status", "--case-id", "QMS-0001",
                    "--format", "text", "--resume-format", "markdown",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, incompatible.returncode)
            self.assertEqual(before, case_path.read_bytes())
            self.assertEqual(git_before, subprocess.run(
                ["git", "-C", temp_dir, "status", "--porcelain=v1", "--untracked-files=all"],
                check=True, capture_output=True, text=True,
            ).stdout)
            status_after = subprocess.run(
                [
                    sys.executable, "-S", "-B", "-m", "quality_loop.cli",
                    "--case-root", temp_dir, "status", "--case-id", "QMS-0001",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, status_after.returncode, status_after.stderr)
            status_after_json = json.loads(status_after.stdout)
            self.assertEqual(status_result["handoff"], status_after_json["handoff"])
            self.assertEqual(status_result["case_revision"], status_after_json["case_revision"])

    def test_contract_error_uses_exit_code_two_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "invalid.json"
            invalid_path.write_text("{}", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    "-B",
                    "-m",
                    "quality_loop.cli",
                    "--case-root",
                    temp_dir,
                    "create-case",
                    "--input",
                    str(invalid_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(2, completed.returncode)
            result = json.loads(completed.stdout)
            self.assertEqual("invalid-input", result["error_code"])
            self.assertFalse(result["state_changed"])

    def test_active_case_auto_discovery_omits_case_id(self) -> None:
        """Phase 5: アクティブ案件が1件の時は--case-idを省略してstatusやreviewを実行できる"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "intake.json"
            input_path.write_text(
                json.dumps(complete_intake(), ensure_ascii=False), encoding="utf-8"
            )
            subprocess.run(
                [
                    sys.executable,
                    "-S",
                    "-B",
                    "-m",
                    "quality_loop.cli",
                    "--case-root",
                    temp_dir,
                    "create-case",
                    "--input",
                    str(input_path),
                ],
                check=True,
                capture_output=True,
            )

            # status without --case-id
            status = subprocess.run(
                [
                    sys.executable,
                    "-S",
                    "-B",
                    "-m",
                    "quality_loop.cli",
                    "--case-root",
                    temp_dir,
                    "status",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, status.returncode, status.stderr)
            status_result = json.loads(status.stdout)
            self.assertEqual("QMS-0001", status_result["case_id"])
            self.assertEqual("reviewer-action", status_result["current_state"])


if __name__ == "__main__":
    unittest.main()
