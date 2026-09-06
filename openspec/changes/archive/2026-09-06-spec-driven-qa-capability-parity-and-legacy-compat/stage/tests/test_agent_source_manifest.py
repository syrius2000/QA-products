import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
import agent_source_manifest


class AgentSourceManifestTest(unittest.TestCase):
    def write_run(self, root: Path) -> Path:
        run_dir = root / "agent-a" / "run-1"
        run_dir.mkdir(parents=True)
        manifest = {"agent_id": "agent-a", "run_id": "run-1"}
        (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        (run_dir / "results.json").write_text(json.dumps({"results": []}), encoding="utf-8")
        return run_dir

    def test_manifest_can_be_verified_without_copying_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "agents"
            self.write_run(root)
            output = Path(directory) / "source-manifest.json"
            report = agent_source_manifest.build_manifest(root)
            output.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(report["status"], "observed")
            self.assertEqual(agent_source_manifest.verify_manifest(output), root.resolve())

    def test_changed_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "agents"
            run_dir = self.write_run(root)
            report = agent_source_manifest.build_manifest(root)
            output = Path(directory) / "source-manifest.json"
            output.write_text(json.dumps(report), encoding="utf-8")
            (run_dir / "results.json").write_text('{"changed": true}', encoding="utf-8")
            with self.assertRaises(ValueError):
                agent_source_manifest.verify_manifest(output)

    def test_added_source_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "agents"
            run_dir = self.write_run(root)
            report = agent_source_manifest.build_manifest(root)
            output = Path(directory) / "source-manifest.json"
            output.write_text(json.dumps(report), encoding="utf-8")
            (run_dir / "added.txt").write_text("new evidence", encoding="utf-8")
            with self.assertRaises(ValueError):
                agent_source_manifest.verify_manifest(output)


if __name__ == "__main__":
    unittest.main()
