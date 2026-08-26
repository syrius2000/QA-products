import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
import agent_aggregator


class AgentAggregatorTest(unittest.TestCase):
    def manifest(self, root: Path, agent: str = "agent-a", run: str = "run-1") -> Path:
        run_dir = root / agent / run
        run_dir.mkdir(parents=True)
        data = {
            "agent_id": agent,
            "run_id": run,
            "model": {"name": "test-model"},
            "prompt_suite_digest": "digest",
            "bundles": {"candidate": {"zip_digest": "candidate-digest"}},
            "cases_total": 1,
            "executed_cases": 1,
            "unexecuted_cases": 0,
            "aggregate": {"candidate": {"avg_tokens": "unverified", "avg_latency": "unverified"}},
        }
        (run_dir / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
        (run_dir / "results.json").write_text(json.dumps({"agent_id": agent, "run_id": run}), encoding="utf-8")
        return run_dir

    def test_separate_runs_and_unverified_metrics_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.manifest(root, "agent-a", "run-1")
            self.manifest(root, "agent-b", "run-1")
            report = agent_aggregator.build_report(root)
            self.assertEqual(report["status"], "observed-with-unverified")
            self.assertEqual(report["agent_count"], 2)
            self.assertEqual(report["run_count"], 2)
            self.assertEqual(report["metric_status_summary"]["latency"], ["unverified"])
            self.assertEqual(report["required_field_status_summary"]["output"]["observed"], 2)

    def test_missing_required_fields_are_reported_as_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = self.manifest(root)
            data = json.loads((run_dir / "manifest.json").read_text())
            data.pop("prompt_suite_digest")
            (run_dir / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            report = agent_aggregator.build_report(root)
            entry = report["agent_runs"][0]
            self.assertEqual(entry["required_field_status"]["prompt_suite"], "unverified")
            self.assertFalse(entry["required_fields_complete"])

    def test_null_timing_and_unexecuted_values_are_unverified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = self.manifest(root)
            data = json.loads((run_dir / "manifest.json").read_text())
            data["started_at"] = None
            data["ended_at"] = None
            data["unexecuted_cases"] = None
            data["aggregate"]["candidate"]["avg_latency"] = "  "
            data["model"] = None
            data["environment"] = "   "
            (run_dir / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            entry = agent_aggregator.build_report(root)["agent_runs"][0]
            self.assertEqual(entry["required_field_status"]["timing"], "unverified")
            self.assertEqual(entry["required_field_status"]["unexecuted_items"], "unverified")
            self.assertEqual(entry["required_field_status"]["conditions"], "unverified")
            self.assertEqual(entry["metrics"]["latency"], "unverified")

    def test_directory_identity_mismatch_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = self.manifest(root)
            data = json.loads((run_dir / "manifest.json").read_text())
            data["run_id"] = "other-run"
            (run_dir / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            report = agent_aggregator.build_report(root)
            self.assertEqual(report["status"], "evidence-gap")
            self.assertTrue(report["errors"])

    def test_nested_results_format_is_accepted_when_identity_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = self.manifest(root)
            (run_dir / "results.json").write_text(
                json.dumps({"results": [{"agent_id": "agent-a", "run_id": "run-1"}]}),
                encoding="utf-8",
            )
            report = agent_aggregator.build_report(root)
            self.assertEqual(report["status"], "observed-with-unverified")
            self.assertEqual(report["run_count"], 1)

    def test_secret_is_not_written_to_aggregate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = self.manifest(root)
            data = json.loads((run_dir / "manifest.json").read_text())
            data["note"] = "token=do-not-store"
            (run_dir / "manifest.json").write_text(json.dumps(data), encoding="utf-8")
            report = agent_aggregator.build_report(root)
            self.assertEqual(report["status"], "evidence-gap")
            self.assertNotIn("do-not-store", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
