# ClaimPilot Harness v0.3 Launch

## One-line pitch

ClaimPilot now evaluates the path an insurance claim Agent takes, not only its final answer.

## What to show

1. Open the [interactive demo](https://samarailly51-pixel.github.io/claimpilot-harness/#trace).
2. Start with `Cautious Trace` and replay the evidence-first workflow.
3. Switch to `Shortcut Trace` and show the blocked unapproved payment attempt.
4. Compare the 100 and 5 trajectory scores and open the full trace report.
5. Explain that every result is deterministic and bound to an executable case workflow.

## Launch copy

ClaimPilot Harness v0.3 is live.

Most Agent evaluations score the final answer. Trace Arena evaluates the actual decision path: which tools were called, which evidence was retrieved, whether actions happened in the right order, and whether dangerous operations passed an approval gate.

In the included bodily injury claim, the cautious trajectory scores 100/100. The shortcut trajectory tries to authorize payment without approval, gets blocked by the tool layer, and scores 5/100.

Try the live demo: https://samarailly51-pixel.github.io/claimpilot-harness/#trace

Source: https://github.com/samarailly51-pixel/claimpilot-harness
