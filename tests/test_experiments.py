import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from claimpilot_harness.experiments import load_profiles, run_arena


class ExperimentTests(unittest.TestCase):
    def test_arena_writes_traceable_baseline_snapshot(self):
        with TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / "profiles.json"
            config.write_text(
                json.dumps({"profiles": [{"id": "safe", "display_name": "Safe", "adapter": "demo"}]}),
                encoding="utf-8",
            )
            result = run_arena("cases/travel-injection-001.json", config, Path(tmpdir) / "out")

            self.assertEqual(result["total_cases"], 1)
            self.assertEqual(result["profiles"][0]["run_type"], "rule_baseline")
            self.assertEqual(result["profiles"][0]["status"], "measured")
            self.assertEqual(len(result["dataset_sha256"]), 64)
            self.assertIsInstance(result["results"][0]["latency_ms"], float)
            self.assertTrue(Path(result["results_file"]).exists())

    def test_arena_marks_missing_external_model_as_skipped(self):
        with TemporaryDirectory() as tmpdir, patch.dict(os.environ, {}, clear=True):
            config = Path(tmpdir) / "profiles.json"
            config.write_text(
                json.dumps({"profiles": [{"id": "external", "adapter": "openai", "model": "example"}]}),
                encoding="utf-8",
            )
            result = run_arena("cases/travel-injection-001.json", config, Path(tmpdir) / "out")

            self.assertEqual(result["profiles"][0]["status"], "skipped")
            self.assertIn("not set", result["profiles"][0]["unavailable_reason"])
            self.assertEqual(result["results"], [])

    def test_profile_config_rejects_duplicate_ids(self):
        with TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / "profiles.json"
            config.write_text(
                json.dumps({"profiles": [{"id": "same", "adapter": "demo"}, {"id": "same", "adapter": "risky"}]}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate profile id"):
                load_profiles(config)


if __name__ == "__main__":
    unittest.main()
