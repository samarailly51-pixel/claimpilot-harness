# ClaimPilot Harness v0.4: Bring Your Own Agent

ClaimPilot v0.4 turns the evaluation engine into a reusable developer product.

## What changed

- Initialize a complete evaluation project with `claimpilot init`.
- Test command, HTTP, and OpenAI-compatible Agents with one `claimpilot test` command.
- Enforce deterministic average-score and pass-rate quality gates in local development and CI.
- Generate an inspectable HTML report and a portable SVG benchmark card after every run.
- Export a disclosure-aware submission artifact for the public Agent Reliability Challenge.
- Build and verify wheel and source distributions before release.
- Publish through PyPI Trusted Publishing without a long-lived API token.

Maintainer release setup is documented in [Publishing ClaimPilot Harness](publishing.md).

## Why it matters

Earlier releases proved the scoring, replay, Model Arena, and Trace Arena concepts. v0.4 removes the adoption gap: another developer can now connect an Agent, reproduce a dataset-bound score, inspect the failures, and share the evidence without learning the internal module layout.

Deterministic scoring remains the default. The score is a regression signal, not a production certification, and the generated report preserves adapter type, dataset fingerprint, unavailable profiles, and disclosure language.
