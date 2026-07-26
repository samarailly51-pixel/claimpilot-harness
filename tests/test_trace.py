import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from claimpilot_harness.cases import load_case
from claimpilot_harness.trace import run_trace, run_trace_arena, score_trace


class TraceTests(unittest.TestCase):
    def setUp(self):
        self.case = load_case("cases/auto-bodily-injury-001.json")

    def test_cautious_trace_passes_workflow_rubric(self):
        trace = run_trace(self.case, "cautious")
        score = score_trace(trace)

        self.assertEqual(score["grade"], "pass")
        self.assertEqual(score["percent"], 100.0)
        self.assertFalse(score["safety_violations"])
        self.assertEqual(trace.decision.verdict, "investigate")

    def test_shortcut_trace_blocks_unapproved_payment(self):
        trace = run_trace(self.case, "shortcut")
        score = score_trace(trace)
        payment_result = next(
            event for event in trace.events if event.event_type == "tool_result" and event.name == "authorize_payment"
        )

        self.assertEqual(payment_result.status, "blocked")
        self.assertEqual(score["grade"], "fail")
        self.assertIn("dangerous tool attempted without human approval", score["safety_violations"])

    def test_trace_arena_writes_json_and_html(self):
        with TemporaryDirectory() as tmpdir:
            result = run_trace_arena(
                "cases/auto-bodily-injury-001.json",
                ["cautious", "shortcut"],
                tmpdir,
            )

            self.assertTrue(Path(result["results_file"]).exists())
            self.assertTrue(Path(result["report"]).exists())
            self.assertEqual(len(result["results"]), 2)

    def test_trace_cli_outputs_machine_readable_result(self):
        with TemporaryDirectory() as tmpdir:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "claimpilot_harness",
                    "trace",
                    "cases/auto-bodily-injury-001.json",
                    "--out",
                    tmpdir,
                    "--json",
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            payload = json.loads(completed.stdout)

            self.assertEqual(payload["case_id"], "auto-bodily-injury-001")
            self.assertEqual(payload["results"][0]["agent"], "cautious")


if __name__ == "__main__":
    unittest.main()
