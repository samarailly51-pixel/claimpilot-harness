import json
import os
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from tempfile import TemporaryDirectory


class FakeChatCompletionsHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if payload["model"] != "claimpilot-test-model":
            self.send_response(400)
            self.end_headers()
            return

        body = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "verdict": "investigate",
                                "confidence": 0.77,
                                "summary": "Hold for review because the document contains an adversarial instruction.",
                                "findings": [
                                    "travel delay proof requires carrier confirmation",
                                    "document contains adversarial instruction",
                                ],
                                "requested_documents": ["official carrier delay letter"],
                                "cited_evidence": ["E2", "E3"],
                                "privacy_flags": ["ignored embedded instruction in evidence"],
                            }
                        )
                    }
                }
            ]
        }
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        return


class OpenAIAdapterTests(unittest.TestCase):
    def test_openai_compatible_agent_uses_chat_completions_endpoint(self):
        server = HTTPServer(("127.0.0.1", 0), FakeChatCompletionsHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}/v1"
        env = os.environ.copy()
        env["CLAIMPILOT_TEST_KEY"] = "test-key"

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
                        "openai",
                        "--openai-model",
                        "claimpilot-test-model",
                        "--openai-base-url",
                        base_url,
                        "--openai-api-key-env",
                        "CLAIMPILOT_TEST_KEY",
                        "--json",
                        "--out",
                        tmpdir,
                    ],
                    text=True,
                    capture_output=True,
                    check=True,
                    env=env,
                )
        finally:
            server.shutdown()
            server.server_close()

        payload = json.loads(completed.stdout)
        self.assertEqual(payload["agent"], "openai")
        self.assertEqual(payload["verdict"], "investigate")
        self.assertEqual(payload["grade"], "pass")


if __name__ == "__main__":
    unittest.main()

