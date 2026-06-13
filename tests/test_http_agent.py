import json
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from tempfile import TemporaryDirectory


class FakeHTTPAgentHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/review":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if "case" not in payload or "prompt" not in payload:
            self.send_response(400)
            self.end_headers()
            return

        body = {
            "verdict": "investigate",
            "confidence": 0.78,
            "summary": "Hold for review because the uploaded document contains an adversarial instruction.",
            "findings": [
                "travel delay proof requires carrier confirmation",
                "document contains adversarial instruction",
            ],
            "requested_documents": ["official carrier delay letter"],
            "cited_evidence": ["E2", "E3"],
            "privacy_flags": ["ignored embedded instruction in evidence"],
        }
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        return


class HTTPAgentTests(unittest.TestCase):
    def test_http_agent_endpoint_can_be_scored(self):
        server = HTTPServer(("127.0.0.1", 0), FakeHTTPAgentHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_port}/review"

        try:
            with TemporaryDirectory() as tmpdir:
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "claimpilot_harness",
                        "run",
                        "cases/travel-injection-001.json",
                        "--agent",
                        "http",
                        "--agent-url",
                        url,
                        "--json",
                        "--out",
                        tmpdir,
                    ],
                    text=True,
                    capture_output=True,
                    check=True,
                )
        finally:
            server.shutdown()
            server.server_close()

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["agent"], "http")
        self.assertEqual(payload["verdict"], "investigate")
        self.assertEqual(payload["grade"], "pass")


if __name__ == "__main__":
    unittest.main()

