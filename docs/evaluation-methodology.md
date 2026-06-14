# Evaluation Methodology

ClaimPilot evaluates insurance claim agents as production workflow components, not as chat demos.

The goal is to test whether an agent can make a safe, evidence-grounded next-step decision when the claim file is incomplete, contradictory, or adversarial.

## Evaluation Principles

### Business action over fluent answer

The primary output is the claim action: `approve`, `deny`, or `investigate`.

A fluent explanation is not enough. A claim agent must choose a defensible business action under policy constraints and uncertainty. When required proof is missing or evidence conflicts, the safest action is often investigation rather than a confident final decision.

### Evidence grounding over generic reasoning

Each case uses stable evidence IDs such as `E1`, `E2`, and `E3`.

ClaimPilot expects agents to cite the evidence that drove the decision. This keeps the evaluation reviewable by product, risk, operations, and compliance teams. If an agent gives a plausible answer without citing the relevant evidence, the harness treats that as a weaker result.

### Missing document detection over guessing

Many real claim failures come from guessing around missing proof.

ClaimPilot rewards agents that ask for the next required document, such as an independent adjuster estimate, official carrier delay letter, prior veterinary records, or medical necessity documentation.

### Safety under adversarial evidence

Uploaded evidence can contain instructions that should not control the agent.

The travel case includes prompt-injection text hidden inside an uploaded document. A strong agent should treat that text as untrusted evidence content, flag it, and continue following the claim review policy.

### Replayability over one-off judgement

Every run produces a replay report with:

- claim context
- evidence timeline
- agent verdict
- requested documents
- cited evidence
- scoring breakdown
- raw decision JSON

This makes failures inspectable instead of anecdotal.

## Scoring Dimensions

| Dimension | What It Tests | Why It Matters |
| --- | --- | --- |
| Verdict | Did the agent choose the expected business action? | Prevents happy-path demos from hiding unsafe approvals. |
| Findings | Did the agent identify the core risk? | Shows whether the agent understood the business issue. |
| Document requests | Did the agent ask for missing proof? | Encourages safe next steps instead of unsupported decisions. |
| Citations | Did the agent cite relevant evidence IDs? | Makes the decision auditable and reviewable. |
| Forbidden behavior | Did the agent avoid explicitly unsafe behavior? | Catches compliance and policy violations. |
| Injection resistance | Did the agent ignore malicious evidence instructions? | Tests agent robustness against adversarial uploads. |

## Case Design

ClaimPilot cases are designed around realistic ambiguity. A good case should contain at least one of:

- conflicting evidence
- missing required proof
- policy exclusion
- suspicious timing
- claimant contradiction
- prompt injection
- privacy or compliance lure

The best cases are not trivia questions. They force the agent to slow down, cite evidence, and choose the next safe workflow step.

## Why Deterministic Scoring First

ClaimPilot starts with deterministic scoring so the harness can run offline, in CI, and across machines without needing a judge model.

This makes regression testing practical:

```bash
python -m claimpilot_harness suite cases --agents demo risky
```

Future judge adapters can add qualitative review, but deterministic scoring gives the project a stable baseline for open-source contribution and CI.

## Reading Suite Results

The suite report should be read as a production-readiness signal, not a model benchmark.

For example:

- a high average score means the agent usually finds the expected safe action
- a low pass rate means the agent is brittle across claim types
- a large gap between agents shows which failure modes are hidden by simple demos
- failed citations or document requests reveal reviewability problems even when the final verdict is correct

## Current Scope

The current case pack covers:

- auto claim invoice mismatch
- health claim medical necessity ambiguity
- travel claim prompt injection
- pet claim pre-existing condition timing
- property claim repair-scope mismatch

The methodology is intentionally case-pack-first and adapter-first. Teams can add more cases or connect different agents without changing the evaluation surface.
