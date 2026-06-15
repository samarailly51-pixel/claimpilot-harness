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

    def test_medical_privacy_injection_case_passes_demo_agent(self):
        with TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "claimpilot_harness",
                    "run",
                    "cases/medical-privacy-injection-001.json",
                    "--json",
                    "--out",
                    tmpdir,
                ],
                text=True,
                capture_output=True,
                check=True,
            )

            payload = json.loads(completed.stdout)
            self.assertEqual(payload["case_id"], "medical-privacy-injection-001")
            self.assertEqual(payload["grade"], "pass")
            self.assertEqual(payload["score"], 100.0)

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

    def test_validate_cases_outputs_summary(self):
        completed = subprocess.run(
            [sys.executable, "-m", "claimpilot_harness", "validate", "cases", "--json"],
            text=True,
            capture_output=True,
            check=True,
        )

        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertGreaterEqual(payload["total"], 6)
        self.assertEqual(payload["failed"], 0)

    def test_validate_rejects_unknown_citation(self):
        with TemporaryDirectory() as tmpdir:
            case_path = Path(tmpdir) / "bad-case.json"
            case_path.write_text(
                json.dumps(
                    {
                        "id": "bad-case",
                        "title": "Bad case",
                        "line": "test",
                        "severity": "low",
                        "claimant": {},
                        "policy": {},
                        "evidence": [{"id": "E1", "type": "note", "summary": "Evidence."}],
                        "traps": [],
                        "expected": {
                            "verdict": "investigate",
                            "must_find": [],
                            "must_request": [],
                            "must_cite": ["E9"],
                            "must_not": [],
                        },
                        "scoring": {
                            "pass_threshold": 75,
                            "verdict_weight": 30,
                            "finding_weight": 12,
                            "document_weight": 8,
                            "citation_weight": 6,
                        },
                    }
                ),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [sys.executable, "-m", "claimpilot_harness", "validate", str(case_path), "--json"],
                text=True,
                capture_output=True,
            )

        self.assertEqual(completed.returncode, 1)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["ok"])
        self.assertIn("unknown evidence id", payload["results"][0]["errors"][0])

    def test_catalog_outputs_coverage_json(self):
        completed = subprocess.run(
            [sys.executable, "-m", "claimpilot_harness", "catalog", "cases", "--json"],
            text=True,
            capture_output=True,
            check=True,
        )

        payload = json.loads(completed.stdout)
        self.assertGreaterEqual(payload["total_cases"], 6)
        self.assertIn("auto", payload["lines"])
        self.assertIn("travel", payload["lines"])
        self.assertIn("prompt_injection", payload["traps"])

    def test_catalog_outputs_markdown_table(self):
        completed = subprocess.run(
            [sys.executable, "-m", "claimpilot_harness", "catalog", "cases", "--markdown"],
            text=True,
            capture_output=True,
            check=True,
        )

        self.assertIn("| Case | Line | Severity | Expected Verdict | Traps |", completed.stdout)
        self.assertIn("`travel-injection-001`", completed.stdout)

    def test_suite_outputs_agent_summary_and_report(self):
        with TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "claimpilot_harness",
                    "suite",
                    "cases",
                    "--agents",
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
            self.assertGreaterEqual(payload["total_cases"], 6)
            self.assertEqual(payload["agents"][0]["agent"], "demo")
            self.assertGreater(payload["agents"][0]["average_score"], payload["agents"][1]["average_score"])
            self.assertTrue(Path(payload["results_file"]).exists())
            results_file = Path(tmpdir) / "suite-results.json"
            self.assertTrue(results_file.exists())
            artifact = json.loads(results_file.read_text(encoding="utf-8"))
            self.assertEqual(artifact["report"], "suite-report.html")
            self.assertTrue(artifact["results"][0]["replay"].endswith("-replay.html"))
            self.assertTrue((Path(tmpdir) / "latest.html").exists())


if __name__ == "__main__":
    unittest.main()
