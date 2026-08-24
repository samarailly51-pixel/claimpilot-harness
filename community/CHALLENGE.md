# ClaimPilot Agent Reliability Challenge

Run the same adversarial claim benchmark against your Agent, publish the failure evidence, and submit a reproducible result.

## Enter the challenge

```bash
pip install claimpilot-harness
claimpilot init my-agent-eval
cd my-agent-eval
claimpilot test
```

Replace the generated command Agent or change `claimpilot.json` to an HTTP or OpenAI-compatible profile. A successful run writes:

- `claimpilot-report.html` for case-level inspection
- `claimpilot-scorecard.svg` for a README or social post
- `claimpilot-scorecard.md` for copy-ready sharing
- `claimpilot-submission.json` for this leaderboard

## Submit a result

1. Fork ClaimPilot Harness and create a branch.
2. Copy `claimpilot-submission.json` to `community/submissions/<github-name>-<agent-name>.json`.
3. Run `claimpilot community --check` and `claimpilot community`.
4. Commit the submission and regenerated `community/LEADERBOARD.md`.
5. Open a pull request and include the source repository, Agent configuration, and reproduction command.

## Rules

- Never commit API keys, customer data, private claim files, or hidden system prompts.
- Disclose the provider, model identifier, adapter, and material configuration used for the run.
- Do not hand-edit scores, pass rates, dataset hashes, or experiment metadata.
- Compare rankings only when `dataset_sha256` matches.
- Built-in rule baselines are reference controls and must not be described as model results.
- Maintainers may request a rerun when a result cannot be reproduced or its disclosure is incomplete.

The deterministic score is a regression signal, not a production certification or a substitute for legal, compliance, or human claim review.
