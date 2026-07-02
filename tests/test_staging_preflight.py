import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from scripts.lighthouse_score_gate import check_lighthouse_files
from scripts.staging_preflight import run_preflight


class PreflightHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Permissions-Policy", "camera=(), microphone=()")
        self.end_headers()
        if self.path == "/robots.txt":
            body = b"Sitemap: http://127.0.0.1/sitemap.xml\n"
        elif self.path == "/sitemap.xml":
            body = b"<?xml version='1.0'?><urlset></urlset>"
        else:
            body = b"<main>ok</main>"
        self.wfile.write(body)

    def log_message(self, _format, *args):
        return


class StagingPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), PreflightHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)

    def test_preflight_passes_for_smoke_security_and_small_load(self):
        report = run_preflight(
            self.origin,
            routes=("/", "/matrix/panel-hospitals", "/status", "/sitemap.xml", "/robots.txt"),
            load_path="/status",
            load_requests=4,
            load_concurrency=2,
            max_p95_ms=5000,
        )

        self.assertEqual(report["overall_status"], "passed")
        self.assertEqual(report["smoke"]["status"], "passed")
        self.assertEqual(report["security"]["status"], "passed")
        self.assertEqual(report["load"]["status"], "passed")

    def test_lighthouse_score_gate_requires_all_categories_above_minimum(self):
        passing_payload = {
            "categories": {
                "performance": {"score": 0.9},
                "accessibility": {"score": 1},
                "best-practices": {"score": 0.92},
                "seo": {"score": 0.95},
            }
        }
        failing_payload = {
            "categories": {
                "performance": {"score": 0.89},
                "accessibility": {"score": 1},
                "best-practices": {"score": 0.92},
                "seo": {"score": 0.95},
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            passing = Path(tmp) / "passing.json"
            failing = Path(tmp) / "failing.json"
            passing.write_text(json.dumps(passing_payload))
            failing.write_text(json.dumps(failing_payload))

            self.assertEqual(check_lighthouse_files((passing,), minimum=0.9)["status"], "passed")
            self.assertEqual(check_lighthouse_files((failing,), minimum=0.9)["status"], "failed")


if __name__ == "__main__":
    unittest.main()
