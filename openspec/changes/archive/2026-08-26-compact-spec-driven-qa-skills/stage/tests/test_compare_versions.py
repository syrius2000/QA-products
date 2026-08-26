#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from compare_versions import compare


class CompareVersionsTest(unittest.TestCase):
    def test_spec_authority_and_equivalent_results(self) -> None:
        source = Path(__file__).resolve().parents[1] / "fixtures/comparison/sample-results.json"
        report = compare(json.loads(source.read_text(encoding="utf-8")))
        self.assertTrue(report["candidate_behavior_is_not_authority"])
        decisions = {item["id"]: item["decision"] for item in report["decisions"]}
        self.assertEqual(decisions["valid-review"], "behavior-diff")
        self.assertEqual(decisions["author-direct-write"], "behavior-diff")
        self.assertTrue(all(not item["spec_violations"] for item in report["decisions"]))

    def test_spec_violation_wins_over_behavior_match(self) -> None:
        payload = {
            "authority": {"spec": "spec.md", "rule": "spec_compliance_overrides_candidate_behavior"},
            "cases": [{"id": "case", "expected": {"exit_code": 0, "contract": "v1.2", "state": "ok", "side_effects": []}}],
            "results": {"legacy": {"case": {"exit_code": 0, "contract": "v1.2", "state": "ok", "side_effects": [], "spec_compliant": True}},
                        "candidate": {"case": {"exit_code": 0, "contract": "v1.2", "state": "ok", "side_effects": [], "spec_compliant": False}}},
        }
        self.assertEqual(compare(payload)["decisions"][0]["decision"], "nonconformant")


if __name__ == "__main__":
    unittest.main()
