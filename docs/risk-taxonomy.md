# Risk Taxonomy

ClaimPilot cases use lightweight `tags` to describe the risk patterns each case exercises. Tags make the case pack easier to scan, compare, and extend as a benchmark.

Tags are not scoring rules by themselves. They are coverage metadata that help reviewers answer:

- Which failure modes does this case pack already cover?
- Which risks are overrepresented or missing?
- Which cases should be used for a focused regression run?
- What new case would add meaningful coverage?

## Current Tags

| Tag | Meaning |
| --- | --- |
| `claimant_contradiction` | Claimant statements conflict with evidence or prior statements. |
| `coverage_timing` | Dates, waiting periods, or enrollment timing affect eligibility. |
| `evidence_conflict` | Two or more evidence items point in different directions. |
| `invoice_mismatch` | A bill or estimate does not match physical or policy evidence. |
| `medical_necessity` | The case depends on whether treatment necessity is documented. |
| `missing_document` | A required proof item is absent or non-authoritative. |
| `policy_exclusion` | A policy exclusion may apply and must be checked. |
| `pre_existing_condition` | Symptoms or conditions may predate coverage. |
| `privacy_lure` | The claimant or document tries to pull in unrelated private data. |
| `prompt_injection` | Evidence contains instructions that try to override agent policy. |
| `scope_inflation` | Claimed repair scope appears broader than supported damage. |
| `untrusted_evidence` | A document is plausible but not authoritative enough to decide. |

## Case Format

Add tags near the top of each case:

```json
{
  "id": "travel-injection-001",
  "line": "travel",
  "severity": "critical",
  "tags": ["missing_document", "prompt_injection", "untrusted_evidence"]
}
```

Use lowercase words with hyphens or underscores. Prefer existing tags when possible, and add a new tag only when it describes a reusable risk pattern.

## Using Tags

Generate a coverage view:

```bash
python -m claimpilot_harness catalog cases
```

Run the suite and inspect machine-readable tags in `suite-results.json`:

```bash
python -m claimpilot_harness suite cases --agents demo risky --json
```

The taxonomy is intentionally small. It should make the benchmark more legible without turning case authoring into heavy governance.
