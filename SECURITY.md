# Security

ClaimPilot Harness includes adversarial examples such as prompt injection, but the repository should never contain real claim data, personal data, medical records, or financial identifiers.

## Reporting Issues

If you find a security issue, please open a private advisory once the GitHub repository is created. Until then, contact the maintainer directly.

## Data Safety

- Use fictional people, policies, invoices, and medical details.
- Do not commit secrets, API keys, real claim files, or customer records.
- Treat uploaded evidence examples as untrusted text.
- Agent adapters should avoid sending case data to third-party APIs unless the user explicitly configures that behavior.

