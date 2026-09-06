import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import runner


class RunnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage = Path(__file__).parents[1]

    def test_fixture_suite_has_five_stable_inputs(self):
        fixtures = runner.load_fixture_suite(self.stage)
        self.assertEqual(tuple(fixtures), runner.FIXTURE_CLASSES)
        self.assertEqual(len({item["digest"] for item in fixtures.values()}), 5)

    def test_only_compact_has_declared_json_adapter(self):
        fixture = runner.load_fixture_suite(self.stage)["golden"]
        compact_root = Path("/tmp/compact-bundle")
        command, reason, environment = runner.adapter_for("compact", "golden", compact_root, Path("input.json"), Path("/tmp"))
        self.assertIsNotNone(command)
        self.assertEqual(reason, "compact JSON Launcher")
        self.assertEqual(environment, {})
        legacy_command, legacy_reason, _ = runner.adapter_for("legacy", "golden", compact_root, Path("input.json"), Path("/tmp"))
        self.assertIsNotNone(legacy_command)
        self.assertIn("create_review_case.py", legacy_reason)
        self.assertEqual(fixture["class"], "golden")

    def test_run_records_all_required_snapshots_and_unverified_gaps(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            manifest = runner.build_run(stage=self.stage, output_root=output, run_id="test-run", selected=("legacy", "candidate"))
            self.assertEqual(manifest["run_count"], 10)
            self.assertEqual(manifest["observed_count"], 10)
            self.assertEqual(manifest["unverified_count"], 0)
            for bundle in ("legacy", "candidate"):
                for fixture_class in runner.FIXTURE_CLASSES:
                    run_dir = output / bundle / fixture_class
                    for name in ("input.json", "stdout.txt", "stderr.txt", "exit_code.json", "structured-output.json", "state-snapshot.json", "side-effects-snapshot.json", "result.json"):
                        self.assertTrue((run_dir / name).is_file(), name)
                    result = json.loads((run_dir / "result.json").read_text())
                    self.assertEqual(result["execution_status"], "observed")

    def test_nonempty_output_and_unsafe_run_id_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run"
            output.mkdir()
            (output / "existing").write_text("x")
            with self.assertRaisesRegex(ValueError, "not empty"):
                runner.build_run(stage=self.stage, output_root=output, run_id="test-run", selected=("legacy",))
            with self.assertRaisesRegex(ValueError, "run_id"):
                runner.build_run(stage=self.stage, output_root=Path(directory) / "other", run_id="../escape", selected=("legacy",))

    def test_bundle_materialization_is_not_reported_as_side_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "legacy-bundle" / "old").mkdir(parents=True)
            (root / "legacy-bundle" / "old" / "payload").write_text("bundle")
            (root / "case").mkdir()
            (root / "case" / "review.md").write_text("generated")
            snapshot = runner.file_snapshot(root, excluded_parts={"legacy-bundle"})
            self.assertEqual([item["path"] for item in snapshot], ["case/review.md"])


if __name__ == "__main__":
    unittest.main()
