## Summary

## Verification

- [ ] `python -m unittest discover -s tests`
- [ ] `python -m claimpilot_harness validate cases`
- [ ] `python -m claimpilot_harness catalog cases`
- [ ] `python -m claimpilot_harness suite cases --agents demo risky`

## Case-pack checklist

- [ ] New or changed cases use fictional data only.
- [ ] `expected.must_cite` references valid evidence IDs.
- [ ] New cases include `expected` and `scoring` blocks.
- [ ] Red-team traps are documented when present.

## Notes for reviewers
