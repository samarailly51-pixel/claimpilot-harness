# OpenAI-Compatible Adapter

ClaimPilot can call any service that exposes an OpenAI-style `/v1/chat/completions` endpoint.

That includes OpenAI-compatible gateways and many local or self-hosted runtimes.

## Environment

Set an API key:

```bash
export OPENAI_API_KEY="..."
```

On PowerShell:

```powershell
$env:OPENAI_API_KEY="..."
```

## Run One Agent

```bash
python -m claimpilot_harness run cases/travel-injection-001.json \
  --agent openai \
  --openai-model your-model-name
```

## Compare Against Baselines

```bash
python -m claimpilot_harness compare cases/travel-injection-001.json demo openai risky \
  --openai-model your-model-name
```

## Custom Base URL

Use `--openai-base-url` for OpenAI-compatible local or hosted gateways:

```bash
python -m claimpilot_harness run cases/travel-injection-001.json \
  --agent openai \
  --openai-model your-model-name \
  --openai-base-url http://localhost:11434/v1
```

## Custom API Key Variable

```bash
python -m claimpilot_harness run cases/travel-injection-001.json \
  --agent openai \
  --openai-model your-model-name \
  --openai-api-key-env CLAIMPILOT_API_KEY
```

The model must return a JSON object with:

```json
{
  "verdict": "investigate",
  "confidence": 0.82,
  "summary": "Hold the claim pending additional review.",
  "findings": ["document contains adversarial instruction"],
  "requested_documents": ["official carrier delay letter"],
  "cited_evidence": ["E2", "E3"],
  "privacy_flags": ["ignored embedded instruction in evidence"]
}
```

ClaimPilot strips common Markdown code fences before parsing, but the cleanest agent output is plain JSON.

