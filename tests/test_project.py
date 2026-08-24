import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from claimpilot_harness.project import (
    evaluate_profile_gate,
    init_project,
    load_project_config,
    render_scorecard_from_results,
    run_project,
)


class ProjectWorkflowTests(unittest.TestCase):
    def test_init_creates_command_project_without_overwriting(self):
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "my-agent"
            result = init_project(target, name="Claims Safety Agent")

            self.assertEqual(result["adapter"], "command")
            self.assertTrue((target / "claimpilot.json").exists())
            self.assertTrue((target / "claimpilot_agent.py").exists())
            self.assertTrue((target / "cases" / "starter-travel-injection.json").exists())
            self.assertTrue((target / ".github" / "workflows" / "claimpilot.yml").exists())
            config = json.loads((target / "claimpilot.json").read_text(encoding="utf-8"))
            self.assertEqual(config["project"], "Claims Safety Agent")
            self.assertEqual(config["profiles"][0]["command"], "{python} claimpilot_agent.py")

            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                init_project(target)

    def test_init_supports_http_and_openai_profiles(self):
        with TemporaryDirectory() as tmpdir:
            http_dir = Path(tmpdir) / "http"
            openai_dir = Path(tmpdir) / "openai"
            init_project(http_dir, adapter="http")
            init_project(openai_dir, adapter="openai")

            http_config = json.loads((http_dir / "claimpilot.json").read_text(encoding="utf-8"))
            openai_config = json.loads((openai_dir / "claimpilot.json").read_text(encoding="utf-8"))
            self.assertEqual(http_config["profiles"][0]["adapter"], "http")
            self.assertEqual(openai_config["profiles"][0]["adapter"], "openai")
            self.assertFalse((http_dir / "claimpilot_agent.py").exists())

    def test_generated_project_runs_end_to_end_and_writes_shareable_artifacts(self):
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "agent-project"
            init_project(target, name="Starter Agent")
            result = run_project(target / "claimpilot.json")

            self.assertTrue(result["quality_gate"]["ok"])
            self.assertEqual(result["total_cases"], 1)
            self.assertEqual(result["profiles"][0]["id"], "my-agent")
            self.assertEqual(result["profiles"][0]["run_type"], "external_model")
            self.assertEqual(result["profiles"][0]["average_score"], 100.0)
            self.assertEqual(result["profiles"][0]["pass_rate"], 100.0)

            out_dir = target / "runs" / "claimpilot"
            for filename in (
                "claimpilot-results.json",
                "claimpilot-report.html",
                "claimpilot-scorecard.svg",
                "claimpilot-scorecard.md",
                "claimpilot-submission.json",
                "latest.html",
            ):
                self.assertTrue((out_dir / filename).exists(), filename)
            self.assertIn("QUALITY GATE PASS", (out_dir / "claimpilot-scorecard.svg").read_text(encoding="utf-8"))
            self.assertIn("Open replay", (out_dir / "claimpilot-report.html").read_text(encoding="utf-8"))

    def test_scorecard_can_be_regenerated_from_results(self):
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "agent-project"
            regenerated = Path(tmpdir) / "regenerated"
            init_project(target)
            result = run_project(target / "claimpilot.json")

            artifacts = render_scorecard_from_results(result["results_file"], regenerated)

            self.assertEqual(Path(artifacts["scorecard"]).parent, regenerated)
            self.assertTrue(Path(artifacts["scorecard"]).exists())
            self.assertTrue(Path(artifacts["submission"]).exists())

    def test_project_config_rejects_invalid_quality_gate(self):
        with TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "agent-project"
            init_project(target)
            config_path = target / "claimpilot.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["quality_gate"]["min_average_score"] = 101
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "0 to 100"):
                load_project_config(config_path)

    def test_quality_gate_reports_profile_failures(self):
        gate = evaluate_profile_gate(
            [
                {
                    "id": "unsafe-agent",
                    "status": "measured",
                    "average_score": 42.0,
                    "pass_rate": 10.0,
                }
            ],
            min_average_score=80,
            min_pass_rate=90,
        )

        self.assertFalse(gate["ok"])
        self.assertEqual(gate["failures"][0]["profile"], "unsafe-agent")
        self.assertEqual(len(gate["failures"][0]["reasons"]), 2)


if __name__ == "__main__":
    unittest.main()
