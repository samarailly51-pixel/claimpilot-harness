# Three-Minute Quickstart

ClaimPilot can scaffold a complete Agent evaluation project without framework dependencies.

## Install and initialize

```bash
pip install claimpilot-harness
claimpilot init my-agent-eval
cd my-agent-eval
claimpilot test
```

The generated project contains:

```text
my-agent-eval/
  claimpilot.json
  claimpilot_agent.py
  cases/starter-travel-injection.json
  .github/workflows/claimpilot.yml
```

The starter command Agent is intentionally small. It reads a JSON payload from `stdin` and prints one decision object to `stdout`. Replace its rule logic with your Agent call while keeping the decision contract.

## Connect another adapter

Generate an HTTP starter:

```bash
claimpilot init my-http-eval --adapter http
```

Generate an OpenAI-compatible starter:

```bash
claimpilot init my-model-eval --adapter openai
```

Then edit the generated profile in `claimpilot.json`. API keys remain in environment variables and must never be committed.

## Project configuration

```json
{
  "schema_version": "1.0",
  "project": "my-agent-eval",
  "cases": "cases",
  "output": "runs/claimpilot",
  "profiles": [
    {
      "id": "my-agent",
      "display_name": "My Claim Agent",
      "provider": "Custom",
      "adapter": "command",
      "command": "{python} claimpilot_agent.py"
    }
  ],
  "quality_gate": {
    "min_average_score": 80,
    "min_pass_rate": 100
  },
  "scorecard_profile": "my-agent"
}
```

Relative command paths run from the directory containing `claimpilot.json`. `{python}` resolves to the active Python interpreter, making the same config portable across Windows, macOS, Linux, local virtual environments, and CI.

## Generated evidence

Every `claimpilot test` run writes:

- `claimpilot-report.html`: profile and case-level results with replay links
- `claimpilot-scorecard.svg`: portable visual benchmark card
- `claimpilot-scorecard.md`: copy-ready README or social post
- `claimpilot-submission.json`: machine-readable Community Challenge entry
- `claimpilot-results.json`: complete project result and quality-gate state
- `arena-results.json`: traceable raw Arena snapshot

The command exits with status `1` when the configured quality gate fails, so the same project works as a pull-request check.
