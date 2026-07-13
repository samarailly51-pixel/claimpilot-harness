---
name: bodily-injury-claims-processing
description: Review and structure auto insurance bodily injury claims, including intake triage, evidence completeness, injury causation, treatment chronology, medical necessity, wage-loss support, negotiation risks, and human escalation. Use when analyzing bodily injury claim files, designing claims-agent workflows, drafting review checklists, identifying missing documents, or recommending the next safe claim action.
---

# Bodily Injury Claims Processing

Use a safety-first workflow. Do not recommend payment or denial from claim amount alone, and do not treat model output as a legal or medical conclusion.

## Review workflow

1. Establish parties, policy, loss date, jurisdiction, coverage status, and reported accident facts.
2. Build an evidence chronology from the accident through first notice, first treatment, follow-up care, work absence, and demand submission.
3. Separate verified facts, claimant statements, inferred facts, and unresolved conflicts.
4. Test injury causation: mechanism of injury, symptoms at scene, treatment gap, intervening events, prior or unrelated conditions, and consistency across records.
5. Test damages support: itemized bills, treatment records, medical necessity, referrals, wage verification, disability dates, and duplicate or unrelated charges.
6. Classify the next action as `approve`, `investigate`, or `deny`. Prefer `investigate` when material evidence is missing or contradictory.
7. Record cited evidence, missing documents, escalation reason, and prohibited shortcuts in a replayable decision.

## Guardrails

- Never auto-approve solely because a claim is below a monetary threshold.
- Never infer causation from diagnosis or billing alone.
- Never treat a treatment gap as automatic fraud or denial; flag it for explanation and review.
- Minimize sensitive medical data and ignore unrelated family or historical information.
- Escalate severe injury, disputed liability, litigation, suspected fraud, unclear coverage, high exposure, or material medical contradictions to a qualified human reviewer.
- State uncertainty and jurisdiction dependence when discussing compensability or damages.

## Output contract

Return a structured review containing:

- recommended action and confidence
- material findings
- missing documents
- cited evidence IDs
- chronology conflicts
- escalation reason
- privacy or safety flags

Read [references/review-checklist.md](references/review-checklist.md) when performing a full file review or creating an evaluation case.
