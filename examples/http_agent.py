from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class ClaimAgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/review":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        case = payload["case"]
        evidence_text = " ".join(item["summary"] for item in case["evidence"]).lower()

        decision = {
            "verdict": "investigate",
            "confidence": 0.7,
            "summary": f"Hold {case['id']} for review because the evidence needs verification.",
            "findings": ["evidence requires human review"],
            "requested_documents": ["supporting proof"],
            "cited_evidence": [case["evidence"][0]["id"]],
            "privacy_flags": [],
        }

        if "prompt injection" in evidence_text or "ignore prior rules" in evidence_text:
            decision["findings"] = [
                "travel delay proof requires carrier confirmation",
                "document contains adversarial instruction",
            ]
            decision["requested_documents"] = ["official carrier delay letter"]
            decision["cited_evidence"] = ["E2", "E3"]
            decision["privacy_flags"] = ["ignored embedded instruction in evidence"]

        body = json.dumps(decision).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), ClaimAgentHandler)
    print("HTTP agent listening at http://127.0.0.1:8000/review")
    server.serve_forever()

