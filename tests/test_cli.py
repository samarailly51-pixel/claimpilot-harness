import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class CliTests(unittest.TestCase):
    def test_run_outputs_json_and_replay(self):
        with TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "claimpilot_harness",
                    "run",
                    "cases/travel-injection-001.json",
                    "--json",
                    "--out",
                    tmpdir,
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["case_id"], "travel-injection-001")
            self.assertEqual(payload["grade"], "pass")
            self.assertTrue(Path(payload["report"]).exists())
            self.assertTrue((Path(tmpdir) / "latest.html").exists())

    def test_list_cases(self):
        completed = subprocess.run(
            [sys.executable, "-m", "claimpilot_harness", "list"],
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertIn("auto-collision-001.json", completed.stdout)
        self.assertIn("travel-injection-001.json", completed.stdout)

    def test_compare_outputs_sorted_leaderboard(self):
        with TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "claimpilot_harness",
                    "compare",
                    "cases/travel-injection-001.json",
                    "demo",
                    "risky",
                    "--json",
                    "--out",
                    tmpdir,
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["case_id"], "travel-injection-001")
            self.assertEqual(payload["results"][0]["agent"], "demo")
            self.assertEqual(payload["results"][1]["agent"], "risky")
            self.assertGreater(payload["results"][0]["score"], payload["results"][1]["score"])
            self.assertTrue(Path(payload["leaderboard"]).exists())
            self.assertTrue((Path(tmpdir) / "latest.html").exists())


if __name__ == "__main__":
    unittest.main()
