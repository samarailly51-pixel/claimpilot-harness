"""Starter ClaimPilot command adapter.

Read one ClaimPilot payload from stdin and print one JSON decision to stdout.
Replace the rule logic with your own Agent while preserving the output contract.
"""

import json
import sys


def main() -> None:
    payload = json.load(sys.stdin)
    case = payload["case"]
    evidence = case.get("evidence", [])
    combined = " ".join(item.get("summary", "") for item in evidence).lower()

    findings = []
    requested_documents = []
    cited_evidence = []
    privacy_flags = []

    for item in evidence:
        summary = item.get("summary", "").lower()
        if "not an official carrier confirmation" in summary:
            findings.append("travel delay proof requires carrier confirmation")
            requested_documents.append("official carrier delay letter")
            cited_evidence.append(item["id"])
        if "prompt injection" in summary or "ignore prior" in summary:
            findings.append("document contains adversarial instruction")
            privacy_flags.append("ignored embedded instruction in evidence")
            cited_evidence.append(item["id"])

    decision = {
        "verdict": "investigate" if findings else "approve",
        "confidence": 0.84 if findings else 0.62,
        "summary": (
            "Hold the claim until trusted carrier evidence is verified."
            if findings
            else "The available trusted evidence supports approval."
        ),
        "findings": findings,
        "requested_documents": requested_documents,
        "cited_evidence": cited_evidence,
        "privacy_flags": privacy_flags,
    }
    print(json.dumps(decision))


if __name__ == "__main__":
    main()
