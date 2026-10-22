"""Adapter from the standard library's http.server to WebApp."""
from __future__ import annotations

import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .http_types import HttpRequest
from .security import SECURITY_HEADERS
from .web_app import WebApp


def create_server(host: str, port: int, app: WebApp) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        server_version = "Isoline"

        def _dispatch(self) -> None:
            request = HttpRequest(
                method=self.command,
                path=self.path,
                headers={k.lower(): v for k, v in self.headers.items()},
                body=self.rfile,
            )
            response = app.handle(request)
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(response.body)))
            for name, value in {**SECURITY_HEADERS, **response.headers}.items():
                self.send_header(name, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(response.body)

        do_GET = do_HEAD = do_POST = _dispatch

        def log_message(self, fmt, *args):  # quieter console
            sys.stderr.write("[isoline] " + fmt % args + "\n")

    return ThreadingHTTPServer((host, port), Handler)
