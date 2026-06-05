# Why ClaimPilot Harness

The market does not need another generic AI agent demo. It needs better ways to decide whether an agent is safe enough to use in a real business workflow.

Insurance claims are a strong proving ground because they combine:

- messy evidence
- policy constraints
- missing documents
- claimant contradictions
- fraud risk
- privacy risk
- prompt injection inside uploaded files
- decisions with financial consequences

That makes claims a useful domain for evaluating production-readiness, not just model cleverness.

## Product Thesis

The hard part of enterprise AI is moving from demo to dependable workflow. ClaimPilot focuses on the layer between those two states: repeatable evaluation, replayable failures, and business-readable scoring.

Instead of asking "Can an agent process a claim?", ClaimPilot asks:

- Can it refuse unsafe instructions embedded in evidence?
- Can it distinguish missing proof from proof of denial?
- Can it cite the evidence that drove its decision?
- Can a product, risk, or compliance reviewer understand the failure?
- Can teams compare agents before putting them in front of users?

## Why Harness, Not Agent

A single claim agent is easy to copy. A harness creates leverage:

- Developers can plug in many agents.
- Product teams can define business-specific cases.
- Risk teams can see repeatable failure reports.
- Open-source contributors can add case packs without agreeing on one agent stack.

That is why ClaimPilot is intentionally adapter-first and case-pack-first.

## What Makes A Good Case

A strong ClaimPilot case should include at least one realistic ambiguity:

- evidence conflict
- policy exclusion
- missing document
- suspicious timing
- claimant contradiction
- prompt injection
- privacy lure

The best cases are not trivia questions. They force the agent to slow down, cite evidence, and ask for the next safe step.

