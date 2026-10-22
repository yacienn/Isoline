from __future__ import annotations

from urllib.parse import urlparse

from .http_types import HttpRequest, HttpResponse, json_response
from .scan_controller import ScanController
from .static_files import StaticFiles


class WebApp:
    """Routing table. Knows nothing about sockets or http.server."""

    def __init__(self, scan_controller: ScanController, static_files: StaticFiles) -> None:
        self._scan = scan_controller
        self._static = static_files

    def handle(self, request: HttpRequest) -> HttpResponse:
        path = urlparse(request.path).path
        if request.method == "POST" and path == "/api/scan":
            return self._scan.handle(request)
        if request.method in ("GET", "HEAD"):
            page = self._static.get(path)
            if page is not None:
                return page
        return json_response(404, {"detail": "Not found"})
