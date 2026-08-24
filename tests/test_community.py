import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from claimpilot_harness.community import build_community_leaderboard, validate_submissions


class CommunityBenchmarkTests(unittest.TestCase):
    def test_repository_submission_and_leaderboard_are_valid(self):
        validation = validate_submissions("community/submissions")
        self.assertTrue(validation["ok"])
        self.assertGreaterEqual(validation["total"], 1)

        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "LEADERBOARD.md"
            result = build_community_leaderboard("community/submissions", output)
            self.assertEqual(result["submissions"], validation["total"])
            self.assertIn("Cautious Rule Baseline", output.read_text(encoding="utf-8"))

    def test_invalid_submission_reports_unsafe_score(self):
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "invalid.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "project": "Broken",
                        "experiment_id": "run-1",
                        "generated_at": "2026-01-01T00:00:00Z",
                        "dataset_sha256": "a" * 64,
                        "total_cases": 1,
                        "profile": {
                            "id": "broken",
                            "display_name": "Broken",
                            "provider": "Custom",
                            "adapter": "command",
                            "run_type": "external_model",
                            "average_score": 120,
                            "pass_rate": 100,
                        },
                        "quality_gate": {"ok": True},
                        "disclosure": "Test fixture.",
                    }
                ),
                encoding="utf-8",
            )
            validation = validate_submissions(path)

        self.assertFalse(validation["ok"])
        self.assertIn("0 to 100", validation["results"][0]["errors"][0])


if __name__ == "__main__":
    unittest.main()
