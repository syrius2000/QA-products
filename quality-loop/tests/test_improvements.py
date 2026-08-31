from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from quality_loop import QualityLoop, QualityLoopError
from quality_loop.cli import build_parser
from quality_loop.observation import build_file_manifest, observe_git_changes
from quality_loop.transitions import EXPECTED_ROLE, EXPECTED_STATE
from test_quality_loop import complete_intake


ROOT = Path(__file__).resolve().parents[1]


class ResumeImprovementTest(unittest.TestCase):
    def test_markdown_resume_lists_evidence_gaps_observation_and_next_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            loop = QualityLoop(Path(temp_dir))
            created = loop.create_case(complete_intake())
            loop.review(
                "QMS-0001",
                {
                    "operation_id": "op-review-gap",
                    "actor_id": "reviewer-001",
                    "role": "reviewer",
                    "invocation_id": "inv-reviewer-001",
                    "previous_handoff_id": created["handoff"]["handoff_id"],
                    "expected_case_revision": 1,
                    "findings": [
                        {
                            "finding_id": "F-GAP-001",
                            "classification": "evidence-gap",
                            "severity": "medium",
                            "requirement_ref": "REQ-001",
                            "observed_fact": "実行記録が未提出",
                            "impact": "受入基準を確認できない",
                            "expected_state": "実行記録が登録されている",
                            "verification_method": "独立して記録を確認する",
                            "evidence_refs": [],
                            "unverified_reason": "実行記録を取得できない",
                            "required_evidence": "対象revisionでの実行ログ",
                            "status": "open",
                        }
                    ],
                    "evidence": [],
                },
            )

            loop.status("QMS-0001", resume_format="markdown")
            text = (Path(temp_dir) / "QMS-0001" / "resume.md").read_text(
                encoding="utf-8"
            )

            self.assertIn("Findings", text)
            self.assertIn("F-GAP-001: 対象revisionでの実行ログ", text)
            self.assertIn("次の担当", text)
            self.assertIn("submit-response --case-id QMS-0001", text)
            self.assertIn("正本ではありません", text)


class GitObservationTest(unittest.TestCase):
    def test_explicit_git_observation_reports_tracked_untracked_and_deleted_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._git(root, "init")
            self._git(root, "config", "user.email", "test@example.invalid")
            self._git(root, "config", "user.name", "Quality Loop Test")
            (root / "changed.txt").write_text("before\n", encoding="utf-8")
            (root / "removed.txt").write_text("remove\n", encoding="utf-8")
            self._git(root, "add", ".")
            self._git(root, "commit", "-m", "baseline")

            (root / "changed.txt").write_text("after\n", encoding="utf-8")
            (root / "removed.txt").unlink()
            (root / "new.txt").write_text("untracked\n", encoding="utf-8")

            observation = observe_git_changes(root, "HEAD")

            self.assertEqual("git-readonly", observation["method"])
            self.assertEqual(
                ["changed.txt", "new.txt", "removed.txt"],
                observation["observed_changed_targets"],
            )
            self.assertIn("Gitが観測できる作業ツリーだけを対象とする", observation["limitations"])

    def test_finite_manifest_records_only_requested_files_and_digests(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "artifact.txt").write_text("observed\n", encoding="utf-8")
            (root / "outside.txt").write_text("not requested\n", encoding="utf-8")

            manifest = build_file_manifest(root, ["artifact.txt"])

            self.assertEqual("finite-manifest", manifest["method"])
            self.assertEqual(["artifact.txt"], manifest["scope"])
            self.assertEqual(["artifact.txt"], [item["path"] for item in manifest["files"]])
            self.assertEqual(64, len(manifest["files"][0]["sha256"]))

    def test_observation_rejects_missing_base_ref_and_manifest_path_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaises(QualityLoopError) as git_error:
                observe_git_changes(root, "")
            self.assertEqual("git-base-ref-required", git_error.exception.error_code)

            with self.assertRaises(QualityLoopError) as manifest_error:
                build_file_manifest(root, ["../outside.txt"])
            self.assertEqual(
                "manifest-path-outside-root", manifest_error.exception.error_code
            )

    @staticmethod
    def _git(root: Path, *args: str) -> None:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode:
            raise AssertionError(completed.stderr)


class OperationAssetTest(unittest.TestCase):
    def test_public_operations_match_cli_state_machine_and_assets(self) -> None:
        operations = {
            "create-case": ("intake.schema.json", "intake.json"),
            "review": ("review.schema.json", "review_input.json"),
            "submit-plan": ("submit-plan.schema.json", "submit_plan.json"),
            "review-plan": ("review-plan.schema.json", "review_plan.json"),
            "submit-response": ("response.schema.json", "response_input.json"),
            "verify": ("verify.schema.json", "verify_input.json"),
            "assess-risk": ("assess-risk.schema.json", "assess_risk.json"),
            "adjudicate": ("adjudicate.schema.json", "adjudicate_input.json"),
            "status": ("status.schema.json", "status.json"),
        }
        self.assertEqual(set(operations) - {"create-case", "status"}, set(EXPECTED_ROLE))
        self.assertEqual(set(operations) - {"create-case", "status"}, set(EXPECTED_STATE))
        parser = build_parser()
        for operation, (schema_name, template_name) in operations.items():
            with self.subTest(operation=operation):
                self.assertTrue((ROOT / "schemas" / schema_name).is_file())
                self.assertTrue((ROOT / "templates" / template_name).is_file())
                args = [operation]
                if operation == "create-case":
                    args += ["--input", "input.json"]
                elif operation != "status":
                    args += ["--case-id", "QMS-TEST", "--input", "input.json"]
                parsed = parser.parse_args(args)
                self.assertEqual(operation, parsed.command)

    def test_formal_templates_contain_every_schema_required_field(self) -> None:
        asset_pairs = {
            "intake.schema.json": "intake.json",
            "review.schema.json": "review_input.json",
            "submit-plan.schema.json": "submit_plan.json",
            "review-plan.schema.json": "review_plan.json",
            "response.schema.json": "response_input.json",
            "verify.schema.json": "verify_input.json",
            "assess-risk.schema.json": "assess_risk.json",
            "adjudicate.schema.json": "adjudicate_input.json",
        }
        for schema_name, template_name in asset_pairs.items():
            with self.subTest(schema=schema_name):
                schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
                template = json.loads((ROOT / "templates" / template_name).read_text(encoding="utf-8"))
                self.assertTrue(set(schema["required"]).issubset(template))

    def test_operation_schemas_and_templates_are_json_and_cover_all_public_operations(self) -> None:
        for operation in (
            "create_case",
            "review",
            "submit_response",
            "verify",
            "adjudicate",
            "status",
        ):
            schema = json.loads(
                (ROOT / "schemas" / f"{operation}.schema.json").read_text(
                    encoding="utf-8"
                )
            )
            template = json.loads(
                (ROOT / "templates" / f"{operation}.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual("object", schema["type"])
            self.assertTrue(schema["required"])
            self.assertIsInstance(template, dict)

    def test_examples_cover_the_four_supported_terminal_or_restart_patterns(self) -> None:
        examples = ROOT / "examples"
        expected = {
            "01-standard-cycle",
            "02-evidence-rebuttal",
            "03-regression-detected",
            "04-accepted-with-risk",
        }
        self.assertEqual(expected, {path.name for path in examples.iterdir() if path.is_dir()})
        for name in expected:
            case = json.loads((examples / name / "case.json").read_text(encoding="utf-8"))
            self.assertIn("case_metadata", case)
            self.assertIn("handoff", case)


if __name__ == "__main__":
    unittest.main()
