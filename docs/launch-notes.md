# Launch Notes

Use these notes when sharing ClaimPilot in a natural, open-source way.

## Short Post

I built ClaimPilot Harness, a small open-source eval harness for insurance claim AI agents.

Instead of demoing an agent on a happy path, it crash-tests agents with messy claim files: conflicting evidence, missing documents, policy exclusions, privacy traps, and prompt injection hidden inside uploaded PDFs.

The latest case is a medical reimbursement claim where the agent has to handle medical necessity ambiguity, a privacy lure, and a hidden instruction to approve the claim.

Live demo: https://samarailly51-pixel.github.io/claimpilot-harness/

GitHub: https://github.com/samarailly51-pixel/claimpilot-harness

## Group Message

I made an open-source project called ClaimPilot Harness. It is not another claim-processing agent, but a test harness for claim agents before production.

It runs adversarial insurance cases, scores the agent, and generates replay reports so you can see exactly where the agent failed.

If this direction interests you, feedback or a GitHub star would help a lot:

https://github.com/samarailly51-pixel/claimpilot-harness

## One-Line Tagline

Crash-test insurance claim AI agents before production.

## What To Mention

- adapter-first: supports built-in, command, HTTP, and OpenAI-compatible agents
- case-pack-first: cases are JSON and easy to contribute
- replayable: every failure has an HTML report
- measurable: deterministic scoring plus suite benchmark JSON
- practical: focuses on missing proof, evidence citation, policy ambiguity, privacy, and prompt injection

## What Not To Say

Avoid positioning it as a job-seeking artifact. Share it as a small open-source eval tool and ask for feedback first. Stars can be a soft second ask.
