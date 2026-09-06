import json
import tempfile
import unittest
from pathlib import Path

import diff_classifier


class DiffClassifierTest(unittest.TestCase):
    def setUp(self):
        self.inventory = {
            "schema_version": "feature-surface-inventory-1",
            "feature_count": 43,
            "features": [
                {"feature_id": "reviewer:DOC", "role": "reviewer", "path": "README.md", "legacy_presence": True, "surface_type": "documentation"},
                {"feature_id": "reviewer:CLI", "role": "reviewer", "path": "scripts/check.py", "legacy_presence": True, "surface_type": "executable"},
                {"feature_id": "author:NEW", "role": "author", "path": "scripts/new.py", "legacy_presence": False, "surface_type": "executable"},
            ],
        }
        self.inventory["features"].extend(
            {
                "feature_id": f"author:NEW-{index:02d}",
                "role": "author",
                "path": f"scripts/new-{index:02d}.py",
                "legacy_presence": False,
                "surface_type": "executable",
            }
            for index in range(1, 41)
        )
        self.bundles = {
            "schema_version": "parity-manifest-1",
            "bundles": [
                {"name": name, "files": [{"path": path} for path in paths]}
                for name, paths in {
                    "legacy": {"spec-driven-qa-review/README.md", "spec-driven-qa-review/scripts/check.py"},
                    "candidate": {"spec_driven_qa_reviewer/README.md", "spec_driven_qa_reviewer/scripts/check.py"},
                    "compact": {"spec-driven-qa-review/README.md", "spec-driven-qa-review/scripts/check.py"},
                }.items()
            ],
        }
        self.runs = {
            "run_id": "run-1",
            "runs": [
                {"bundle": {"name": name}, "fixture": {"class": fixture}, "execution_status": "observed"}
                for name in ("legacy", "candidate", "compact")
                for fixture in ("golden", "negative", "cross-skill", "legacy-compat", "size")
            ],
        }
        self.cross = {"run_id": "cross-1", "results": []}
        self.decisions = {"decisions": []}

    def test_build_report_classifies_documentation_and_new_feature(self):
        report = diff_classifier.build_report(self.inventory, self.bundles, self.runs, self.cross, self.decisions)
        by_id = {item["feature_id"]: item for item in report["features"]}
        self.assertEqual(by_id["reviewer:DOC"]["classification"], "compatible")
        self.assertEqual(by_id["author:NEW"]["classification"], "intentional-noncompatibility")
        self.assertEqual(report["overall_status"], "evidence-gap")

    def test_missing_or_unverified_never_becomes_overall_compatible(self):
        self.inventory["features"][1]["path"] = "scripts/missing.py"
        report = diff_classifier.build_report(self.inventory, self.bundles, self.runs, self.cross, self.decisions)
        self.assertEqual(report["overall_status"], "evidence-gap")
        self.assertFalse(report["legacy_full_compatibility"])
        self.assertGreater(report["classification_counts"]["missing-or-unverified"], 0)

    def test_decision_requires_evidence_and_is_separate_from_missing(self):
        self.decisions["decisions"] = [{
            "id": "legacy-gap", "scope": "legacy.cross-skill", "classification": "intentional-noncompatibility",
            "reason": "旧版契約に存在しない", "spec_ref": "spec.md#x", "evidence_ref": "cross-skill.json",
        }]
        report = diff_classifier.build_report(self.inventory, self.bundles, self.runs, self.cross, self.decisions)
        self.assertGreaterEqual(report["classification_counts"]["intentional-noncompatibility"], 2)

    def test_unknown_decision_classification_is_rejected(self):
        self.decisions["decisions"] = [{"id": "bad", "scope": "x", "classification": "unknown"}]
        with self.assertRaisesRegex(ValueError, "unsupported decision classification"):
            diff_classifier.build_report(self.inventory, self.bundles, self.runs, self.cross, self.decisions)

    def test_cli_returns_nonzero_for_unresolved_difference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = {
                "inventory": self.inventory,
                "bundle-manifest": self.bundles,
                "run-manifest": self.runs,
                "cross-skill": self.cross,
                "decisions": self.decisions,
            }
            arguments = []
            for name, value in inputs.items():
                path = root / f"{name}.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                arguments.extend([f"--{name}", str(path)])
            output = root / "report.json"
            arguments.extend(["--output", str(output)])
            self.assertEqual(diff_classifier.main(arguments), 2)
            self.assertEqual(json.loads(output.read_text())["overall_status"], "evidence-gap")


if __name__ == "__main__":
    unittest.main()
