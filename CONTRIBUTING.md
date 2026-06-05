# Contributing

ClaimPilot Harness is case-pack-first. The easiest way to contribute is to add realistic adversarial claim scenarios.

## Good First Contributions

- Add a new case under `cases/`.
- Improve the scoring rubric in an existing case.
- Add an adapter for an agent framework or model runtime.
- Improve replay readability.
- Add tests for scorer behavior.

## Case Pack Guidelines

Good cases should be realistic, specific, and reviewable. Prefer scenarios where a strong claim agent should slow down and ask for more evidence.

A strong case usually includes one or more of:

- conflicting evidence
- missing required document
- policy exclusion
- suspicious timing
- claimant contradiction
- prompt injection hidden in evidence
- privacy or compliance lure

Avoid real personal data. All claimants, policies, files, and events should be fictional.

## Running Tests

```bash
python -m unittest discover -s tests
python -m claimpilot_harness run cases/travel-injection-001.json --json
```

## Pull Request Checklist

- The new behavior has a focused test or smoke test.
- New cases include `expected` and `scoring` blocks.
- Replay output still renders as standalone HTML.
- No real personal, medical, or financial data is included.

