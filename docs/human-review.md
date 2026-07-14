# Human Review Workbench

The GitHub Pages demo includes a local-first review workbench for comparing an Agent recommendation with a human decision.

Each saved record contains the case and Agent identifiers, Agent verdict and score, human verdict, confirmed findings, reviewer rationale, review timestamp, and dataset fingerprint.

Reviews remain in browser `localStorage` until the reviewer exports or clears them. The static demo does not transmit claim or review data to a server.

Exported JSON can become a regression fixture, review audit artifact, or input to a future feedback-learning pipeline. Human review does not overwrite the original deterministic score.
