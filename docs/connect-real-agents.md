# Connect Real Agents

ClaimPilot is adapter-first. You can evaluate a real agent without rewriting the harness.

The agent only needs to return this decision shape:

```json
{
  "verdict": "investigate",
  "confidence": 0.82,
  "summary": "Hold the claim pending additional review.",
  "findings": ["medical necessity is not documented"],
  "requested_documents": ["medical necessity letter"],
  "cited_evidence": ["E2", "E5"],
  "privacy_flags": ["ignored embedded instruction in evidence"]
}
```

## Option 1: OpenAI-Compatible Endpoint

Use this when your model or gateway supports `/v1/chat/completions`.

```bash
set OPENAI_API_KEY=your-api-key
python -m claimpilot_harness run cases/medical-privacy-injection-001.json \
  --agent openai \
  --openai-model your-model-name
```

For compatible gateways, pass a custom base URL:

```bash
python -m claimpilot_harness compare cases/medical-privacy-injection-001.json demo openai risky \
  --openai-model your-model-name \
  --openai-base-url https://your-gateway.example.com/v1
```

## Option 2: HTTP Agent Service

Use this when your agent runs as a local or hosted service.

Start the example service:

```bash
python examples/http_agent.py
```

Evaluate it:

```bash
python -m claimpilot_harness run cases/travel-injection-001.json \
  --agent http \
  --agent-url http://127.0.0.1:8000/review
```

The HTTP service receives:

```json
{
  "case": {},
  "prompt": "..."
}
```

It should return the decision JSON shown at the top of this document.

## Option 3: Command Adapter

Use this for scripts, prototypes, notebooks, or local agents.

```bash
python -m claimpilot_harness run cases/auto-collision-001.json \
  --agent command \
  --agent-command "python examples/simple_agent.py"
```

The command reads JSON from `stdin` and writes a decision JSON object to `stdout`.

## Run A Full Suite

Once the agent works on one case, run the full regression suite:

```bash
python -m claimpilot_harness suite cases --agents demo risky openai \
  --openai-model your-model-name
```

Read:

- `runs/suite-report.html` for a human-readable report
- `runs/suite-results.json` for a machine-readable benchmark artifact

## What To Watch For

Strong claim agents should:

- choose `investigate` when proof is missing or evidence conflicts
- cite evidence IDs instead of giving generic reasoning
- request the next required document
- refuse instructions embedded inside uploaded evidence
- avoid using unrelated private medical information

If an agent gets the verdict right but misses citations, missing documents, or privacy flags, it is not production-ready yet.
