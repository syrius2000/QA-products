from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from quality_loop import QualityLoop
from quality_loop.errors import QualityLoopError
from quality_loop.observation import (
    MAX_MANIFEST_FILE_BYTES,
    compute_file_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


def run_cli(case_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-S",
            "-B",
            "-m",
            "quality_loop.cli",
            "--case-root",
            str(case_root),
            *arguments,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def result_of(completed: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(completed.stdout)


class StandaloneReviewTest(unittest.TestCase):
    def test_cli_help_exposes_standalone_entrypoint_and_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            completed = run_cli(Path(temp_dir), "review-standalone", "--help")
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("--target", completed.stdout)
            self.assertIn("--artifact", completed.stdout)
            self.assertIn("--owner", completed.stdout)

    def test_bootstrap_then_formal_review_preserves_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "Implementation_result.md"
            target.write_text("# 実装結果\n\n確認対象です。\n", encoding="utf-8")
            before = hashlib.sha256(target.read_bytes()).hexdigest()
            case_root = root / "cases"

            boot = run_cli(
                case_root,
                "review-standalone",
                "--artifact",
                str(target),
                "--owner",
                "owner-yamaguchi",
            )
            self.assertEqual(0, boot.returncode, boot.stderr)
            boot_result = result_of(boot)
            self.assertEqual("review-standalone", boot_result["entrypoint"])
            self.assertEqual(1, boot_result["case_revision"])
            self.assertEqual("reviewer", boot_result["next_role"])
            self.assertEqual("review", boot_result["next_action"])
            self.assertEqual([str(target.absolute())], boot_result["review_context"]["targets"])

            review_input = root / "review.json"
            review_input.write_text(
                json.dumps(
                    {
                        "operation_id": "review-standalone-test-001",
                        "actor_id": "reviewer-test",
                        "role": "reviewer",
                        "invocation_id": "reviewer-invocation-001",
                        "previous_handoff_id": boot_result["handoff"]["handoff_id"],
                        "expected_case_revision": 1,
                        "findings": [],
                        "evidence": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            reviewed = run_cli(
                case_root,
                "review",
                "--case-id",
                boot_result["case_id"],
                "--input",
                str(review_input),
            )
            self.assertEqual(0, reviewed.returncode, reviewed.stderr)
            reviewed_result = result_of(reviewed)
            self.assertEqual(2, reviewed_result["case_revision"])
            self.assertEqual("owner", reviewed_result["next_role"])
            self.assertEqual("adjudicate", reviewed_result["next_action"])
            self.assertEqual(before, hashlib.sha256(target.read_bytes()).hexdigest())

    def test_finding_from_standalone_case_uses_formal_plan_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "artifact.md"
            target.write_text("# 対象\n", encoding="utf-8")
            case_root = root / "cases"
            boot = result_of(
                run_cli(
                    case_root,
                    "review-standalone",
                    "--target",
                    str(target),
                    "--owner",
                    "owner-001",
                    "--case-id",
                    "standalone-test-001",
                )
            )
            review_input = root / "review.json"
            review_input.write_text(
                json.dumps(
                    {
                        "operation_id": "review-standalone-test-002",
                        "actor_id": "reviewer-001",
                        "role": "reviewer",
                        "invocation_id": "reviewer-invocation-002",
                        "previous_handoff_id": boot["handoff"]["handoff_id"],
                        "expected_case_revision": 1,
                        "findings": [
                            {
                                "finding_id": "F-001",
                                "classification": "requirement-violation",
                                "severity": "high",
                                "requirement_ref": "STANDALONE-SCOPE-001",
                                "observed_fact": "確認Evidenceがない",
                                "impact": "第三者が結果を再確認できない",
                                "expected_state": "確認可能なEvidenceがある",
                                "verification_method": "Evidence参照を確認する",
                                "evidence_refs": [],
                            }
                        ],
                        "evidence": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            reviewed = run_cli(
                case_root,
                "review",
                "--case-id",
                "standalone-test-001",
                "--input",
                str(review_input),
            )
            self.assertEqual(0, reviewed.returncode, reviewed.stderr)
            reviewed_result = result_of(reviewed)
            self.assertEqual("implementer", reviewed_result["next_role"])
            self.assertEqual("submit-plan", reviewed_result["next_action"])
            self.assertEqual(["F-001"], reviewed_result["handoff"]["open_items"])

    def test_repeated_bootstrap_is_idempotent_and_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "artifact.md"
            other = root / "other.md"
            target.write_text("target\n", encoding="utf-8")
            other.write_text("other\n", encoding="utf-8")
            case_root = root / "cases"
            args = (
                "review-standalone",
                "--target",
                str(target),
                "--owner",
                "owner-001",
                "--case-id",
                "explicit-case-001",
            )
            first = run_cli(case_root, *args)
            second = run_cli(case_root, *args)
            mismatch = run_cli(
                case_root,
                "review-standalone",
                "--target",
                str(other),
                "--owner",
                "owner-001",
                "--case-id",
                "explicit-case-001",
            )
            self.assertEqual(0, first.returncode, first.stderr)
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertEqual(result_of(first)["case_id"], result_of(second)["case_id"])
            self.assertEqual("already-processed", result_of(second)["status"])
            self.assertEqual(3, mismatch.returncode)
            self.assertEqual("standalone-case-mismatch", result_of(mismatch)["error_code"])

    def test_manifest_streams_and_rejects_oversized_target_without_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            one_mib = root / "one-mib.bin"
            ten_mib = root / "ten-mib.bin"
            oversized = root / "oversized.bin"
            one_mib.write_bytes(b"a" * (1024 * 1024))
            ten_mib.write_bytes(b"b" * MAX_MANIFEST_FILE_BYTES)
            oversized.write_bytes(b"c" * (MAX_MANIFEST_FILE_BYTES + 1))

            with patch.object(Path, "read_bytes", side_effect=AssertionError("一括読み込みは禁止")):
                manifest = compute_file_manifest([str(one_mib), str(ten_mib)])
            self.assertEqual(
                hashlib.sha256(one_mib.read_bytes()).hexdigest(),
                manifest[str(one_mib)],
            )
            self.assertEqual(
                hashlib.sha256(ten_mib.read_bytes()).hexdigest(),
                manifest[str(ten_mib)],
            )

            case_root = root / "oversized-cases"
            failed = run_cli(
                case_root,
                "review-standalone",
                "--target",
                str(oversized),
                "--owner",
                "owner-001",
            )
            self.assertEqual(3, failed.returncode)
            failure = result_of(failed)
            self.assertEqual("manifest-target-too-large", failure["error_code"])
            self.assertFalse(failure["state_changed"])
            self.assertFalse(case_root.exists())


class StandaloneApiContractTest(unittest.TestCase):
    def test_directory_and_symlink_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.md"
            target.write_text("target\n", encoding="utf-8")
            link = root / "link.md"
            link.symlink_to(target)
            loop = QualityLoop(root / "cases")

            with self.assertRaises(QualityLoopError) as directory_error:
                loop.review_standalone(
                    {"targets": [str(root)], "owner": "owner-001"}
                )
            self.assertEqual("manifest-target-directory", directory_error.exception.error_code)
            with self.assertRaises(QualityLoopError) as link_error:
                loop.review_standalone(
                    {"targets": [str(link)], "owner": "owner-001"}
                )
            self.assertEqual("manifest-target-not-regular", link_error.exception.error_code)


if __name__ == "__main__":
    unittest.main()
