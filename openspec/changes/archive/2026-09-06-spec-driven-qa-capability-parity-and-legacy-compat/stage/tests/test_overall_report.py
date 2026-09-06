import json
import tempfile
import unittest
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
import overall_report


class OverallReportTest(unittest.TestCase):
    def test_evidence_gap_is_not_promoted_to_observed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in {
                "compatibility-report.json": {"overall_status": "evidence-gap"},
                "safety-regression.json": {"status": "observed"},
                "contract-applicability.json": {"status": "evidence-gap"},
                "candidate-contract-probe.json": {"status": "observed-violation"},
                "candidate-digest-probe.json": {"status": "observed"},
                "agent-aggregate.json": {"status": "observed-with-unverified"},
                "agents/source-manifest.json": {"status": "observed"},
                "size-report.json": {"status": "observed"},
            }.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(value), encoding="utf-8")
            for folder, value in {
                ("runs", "run-1"): {"run_count": 1, "observed_count": 1},
                ("cross-skill", "run-1"): {"status": "evidence-gap"},
            }.items():
                path = root / folder[0] / folder[1]
                path.mkdir(parents=True)
                (path / "manifest.json").write_text(json.dumps(value), encoding="utf-8")
            report = overall_report.build_report(root, "run-1")
            self.assertEqual(report["status"], "evidence-gap")
            self.assertFalse(report["promotion"]["allowed"])
            self.assertEqual(report["decision"], "human-adjudication-required")

            adjudication = root / "human-adjudication.json"
            adjudication.write_text(json.dumps({
                "case_id": "QA-0008",
                "decision": "accepted-with-residual-risk",
                "selected_option": "A",
            }), encoding="utf-8")
            accepted_report = overall_report.build_report(root, "run-1", adjudication)
            self.assertEqual(accepted_report["decision"], "accepted-with-residual-risk")
            self.assertEqual(accepted_report["input_statuses"]["human_adjudication"], "observed")
            self.assertFalse(accepted_report["promotion"]["allowed"])


if __name__ == "__main__":
    unittest.main()
