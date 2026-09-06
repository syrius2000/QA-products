import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import cross_skill


class CrossSkillTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage = Path(__file__).parents[1]

    def test_author_response_is_cycle_scoped_and_not_closed(self):
        text = cross_skill.author_response("QA-0001")
        self.assertIn("action: author-response", text)
        self.assertIn("### QA-0001-F01", text)
        self.assertNotIn("fixed-and-verified", text)

    def test_compact_flow_persists_and_verifies_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest = cross_skill.parity_harness.build_manifest()
            root = cross_skill.parity_harness.repository_root() / next(item for item in manifest["bundles"] if item["name"] == "compact")["source"]
            (output / "input.json").write_text("{}")
            result = cross_skill.compact_flow(root, output / "input.json", output)
            self.assertEqual(result["reviewer"]["status"], "observed")
            self.assertEqual(result["submission"]["status"], "observed")
            self.assertEqual(result["digest"]["status"], "observed")

    def test_run_id_and_fixture_result_schema(self):
        self.assertRegex(cross_skill.runner_digest({"class": "cross-skill"}), r"^[0-9a-f]{64}$")
        with self.assertRaisesRegex(ValueError, "run_id"):
            cross_skill.run_flow(self.stage, Path(tempfile.mkdtemp()) / "out", "../unsafe")


if __name__ == "__main__":
    unittest.main()
