import json
import sys


payload = json.load(sys.stdin)
case = payload["case"]

print(
    json.dumps(
        {
            "verdict": "investigate",
            "confidence": 0.61,
            "summary": f"Manual baseline review for {case['id']}; hold the claim until evidence conflicts are resolved.",
            "findings": ["evidence requires human review"],
            "requested_documents": ["supporting proof"],
            "cited_evidence": ["E1"],
            "privacy_flags": [],
        }
    )
)

