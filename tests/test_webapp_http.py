"""HTTP layer: controller, routing, static files, error mapping, and a real socket round-trip."""
import io
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from isoline.webapp.application.errors import (InvalidApk, ModelNotTrained, ScannerFailure,
                                               ScanTimeout, UploadIncomplete)
from isoline.webapp.application.ports import RawScan
from isoline.webapp.application.scan_apk import ScanApk
from isoline.webapp.infrastructure.temp_upload_storage import TempUploadStorage
from isoline.webapp.interface.http_server import create_server
from isoline.webapp.interface.http_types import HttpRequest
from isoline.webapp.interface.scan_controller import ScanController
from isoline.webapp.interface.static_files import StaticFiles
from isoline.webapp.interface.web_app import WebApp

WEB_DIR = Path(__file__).resolve().parents[1] / "web"


class StubScanner:
    def __init__(self, raw=None, error=None):
        self.raw, self.error = raw, error

    def scan(self, apk_path):
        if self.error:
            raise self.error
        return self.raw


def make_app(scanner, static_dir=WEB_DIR, max_bytes=1024):
    use_case = ScanApk(TempUploadStorage(), scanner, max_bytes)
    return WebApp(ScanController(use_case), StaticFiles(static_dir))


def post(app, body=b"PK", headers=None, path="/api/scan"):
    h = {"host": "127.0.0.1:8000", "content-length": str(len(body))}
    h.update(headers or {})
    return app.handle(HttpRequest("POST", path, h, io.BytesIO(body)))


GOOD = RawScan("a" * 64, 0.9, ("android.permission.SEND_SMS",))


class ScanEndpointTests(unittest.TestCase):
    def test_success_payload_shape(self):
        r = post(make_app(StubScanner(GOOD)))
        self.assertEqual(r.status, 200)
        data = json.loads(r.body)
        self.assertEqual(data["verdict"], "malicious")
        self.assertEqual(data["score"], 90)
        self.assertEqual(data["permissions"], [{"name": "android.permission.SEND_SMS", "risk": "high"}])
        self.assertEqual(data["permission_count"], 1)
        self.assertEqual(data["indicators"][0]["severity"], "high")

    def test_error_mapping(self):
        cases = [(ModelNotTrained("m"), 503), (InvalidApk("x"), 422), (ScanTimeout("t"), 422),
                 (ScannerFailure("c"), 500), (UploadIncomplete("u"), 400)]
        for error, status in cases:
            with self.subTest(error=type(error).__name__):
                r = post(make_app(StubScanner(error=error)))
                self.assertEqual(r.status, status)
                self.assertIn("detail", json.loads(r.body))

    def test_size_limits_and_headers(self):
        app = make_app(StubScanner(GOOD), max_bytes=10)
        self.assertEqual(post(app, body=b"x" * 11).status, 413)
        self.assertEqual(post(app, body=b"").status, 413)
        self.assertEqual(post(app, headers={"content-length": "abc"}).status, 411)
        no_len = HttpRequest("POST", "/api/scan", {"host": "h"}, io.BytesIO(b"x"))
        self.assertEqual(app.handle(no_len).status, 411)

    def test_cross_origin_blocked_same_origin_allowed(self):
        app = make_app(StubScanner(GOOD))
        self.assertEqual(post(app, headers={"origin": "https://evil.example"}).status, 403)
        self.assertEqual(post(app, headers={"origin": "http://127.0.0.1:8000"}).status, 200)

    def test_unknown_routes(self):
        app = make_app(StubScanner(GOOD))
        self.assertEqual(post(app, path="/api/other").status, 404)
        self.assertEqual(app.handle(HttpRequest("GET", "/nope", {}, io.BytesIO())).status, 404)


class StaticFilesTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app(StubScanner(GOOD))

    def get(self, path):
        return self.app.handle(HttpRequest("GET", path, {}, io.BytesIO()))

    def test_serves_page_and_assets_with_right_types(self):
        self.assertEqual(self.get("/").content_type, "text/html; charset=utf-8")
        self.assertEqual(self.get("/index.html").status, 200)
        self.assertEqual(self.get("/css/styles.css").content_type, "text/css; charset=utf-8")
        self.assertEqual(self.get("/js/main.js").content_type, "text/javascript; charset=utf-8")

    def test_blocks_traversal_dotfiles_and_unknown_types(self):
        for path in ("/../README.md", "/%2e%2e/README.md", "/..%2fREADME.md", "/js/../../isoline/policy.py",
                     "/%00", "/js", "/css/"):
            with self.subTest(path=path):
                self.assertEqual(self.get(path).status, 404)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".secret.html").write_text("x")
            (root / "data.txt").write_text("x")
            app = make_app(StubScanner(GOOD), static_dir=root)
            for path in ("/.secret.html", "/data.txt"):
                self.assertEqual(app.handle(HttpRequest("GET", path, {}, io.BytesIO())).status, 404)


class LiveServerTests(unittest.TestCase):
    """Real http.server on a free port with a stub scanner."""

    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0, make_app(StubScanner(GOOD), max_bytes=1 << 20))
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_page_has_security_headers(self):
        with urllib.request.urlopen(self.base + "/") as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
            self.assertIn("default-src 'self'", r.headers["Content-Security-Policy"])
            self.assertEqual(r.headers["X-Frame-Options"], "DENY")

    def test_head_has_no_body(self):
        req = urllib.request.Request(self.base + "/", method="HEAD")
        with urllib.request.urlopen(req) as r:
            self.assertEqual(r.read(), b"")
            self.assertGreater(int(r.headers["Content-Length"]), 0)

    def test_upload_round_trip(self):
        req = urllib.request.Request(self.base + "/api/scan", data=b"PK\x03\x04", method="POST",
                                     headers={"Content-Type": "application/octet-stream"})
        with urllib.request.urlopen(req) as r:
            self.assertEqual(json.loads(r.read())["verdict"], "malicious")

    def test_cross_origin_post_rejected(self):
        req = urllib.request.Request(self.base + "/api/scan", data=b"PK", method="POST",
                                     headers={"Origin": "https://evil.example"})
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(req)
        self.assertEqual(cm.exception.code, 403)


if __name__ == "__main__":
    unittest.main()
