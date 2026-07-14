# Contributing

ClaimPilot Harness is case-pack-first. The easiest way to contribute is to add realistic adversarial claim scenarios.

## Good First Contributions

- Add a new case under `cases/`.
- Improve the scoring rubric in an existing case.
- Add an adapter for an agent framework or model runtime.
- Improve replay readability.
- Add tests for scorer behavior.

Use the [Good first case issue template](.github/ISSUE_TEMPLATE/good_first_case.md) for a guided contribution, or read the [Community Case Pack](docs/community-case-pack.md) workflow.

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

Start from [`cases/template-case.json`](cases/template-case.json), then read the full [Case Contribution Guide](docs/case-contribution-guide.md).

## Running Tests

```bash
python -m unittest discover -s tests
python -m claimpilot_harness validate cases
python -m claimpilot_harness catalog cases
python -m claimpilot_harness suite cases --agents demo risky
python -m claimpilot_harness arena cases --config benchmarks/baseline-arena.json
```

## Pull Request Checklist

- The new behavior has a focused test or smoke test.
- New cases include `expected` and `scoring` blocks.
- New cases are based on fictional data only.
- New cases validate with `python -m claimpilot_harness validate cases`.
- Replay output still renders as standalone HTML.
- No real personal, medical, or financial data is included.
