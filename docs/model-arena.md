# Model Arena

Model Arena runs named Agent profiles against the same case pack and writes a traceable benchmark snapshot.

## Run the public baselines

```bash
python -m claimpilot_harness arena cases \
  --config benchmarks/baseline-arena.json \
  --out runs/arena
```

The artifact records the experiment timestamp, dataset SHA-256 fingerprint, profile metadata, average score, pass rate, median latency, case-level result, and replay path.

Built-in `demo` and `risky` adapters are labeled `rule_baseline`. OpenAI-compatible, HTTP, and command adapters are labeled `external_model`. ClaimPilot never changes that label based on a display name.

## Connect real models

Copy `benchmarks/models.example.json` to `benchmarks/models.json`, enable the profiles you can run, and set credentials only through the named environment variable.

```bash
python -m claimpilot_harness arena cases \
  --config benchmarks/models.json \
  --out runs/arena-real \
  --require-all
```

`--require-all` makes missing credentials or endpoints fail the experiment. Without it, unavailable profiles are preserved as `skipped` with a reason.

API keys are never written to the result artifact. Token and cost fields remain `null` when an adapter does not return verified usage data.
