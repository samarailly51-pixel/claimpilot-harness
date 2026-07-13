import unittest

from claimpilot_harness.agents import demo_agent, extract_json_object
from claimpilot_harness.cases import load_case
from claimpilot_harness.scorer import score_decision


class ScorerTests(unittest.TestCase):
    def test_demo_agent_passes_prompt_injection_case(self):
        case = load_case("cases/travel-injection-001.json")
        decision = demo_agent(case)
        score = score_decision(case, decision)

        self.assertEqual(decision.verdict, "investigate")
        self.assertEqual(score["grade"], "pass")
        self.assertGreaterEqual(score["percent"], 80)
        self.assertTrue(
            any(check["name"] == "prompt injection resistance" and check["passed"] for check in score["checks"])
        )

    def test_missing_required_findings_fails(self):
        case = load_case("cases/auto-collision-001.json")
        decision = demo_agent(case)
        weak_decision = decision.__class__(
            verdict="approve",
            confidence=0.91,
            summary="Approve without review.",
            findings=[],
            requested_documents=[],
            cited_evidence=[],
            privacy_flags=[],
        )
        score = score_decision(case, weak_decision)

        self.assertEqual(score["grade"], "fail")
        self.assertLess(score["percent"], 75)

    def test_bodily_injury_skill_case_passes_demo_agent(self):
        case = load_case("cases/auto-bodily-injury-001.json")
        decision = demo_agent(case)
        score = score_decision(case, decision)

        self.assertEqual(decision.verdict, "investigate")
        self.assertEqual(score["grade"], "pass")
        self.assertGreaterEqual(score["percent"], 80)
        self.assertIn("employer wage verification", decision.requested_documents)

    def test_extract_json_object_from_fenced_model_response(self):
        raw = """```json
{
  "verdict": "investigate",
  "confidence": 0.8,
  "summary": "Hold for review.",
  "findings": [],
  "requested_documents": [],
  "cited_evidence": [],
  "privacy_flags": []
}
```"""

        parsed = extract_json_object(raw)

        self.assertEqual(parsed["verdict"], "investigate")
        self.assertEqual(parsed["confidence"], 0.8)


if __name__ == "__main__":
    unittest.main()
