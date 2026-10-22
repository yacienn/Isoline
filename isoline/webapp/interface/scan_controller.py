from __future__ import annotations

from ..application.errors import ScanError
from ..application.scan_apk import ScanApk
from .http_types import HttpRequest, HttpResponse, json_response
from .presenters import present_error, present_report
from .security import is_cross_origin


class ScanController:
    """POST /api/scan - body is the raw APK bytes."""

    def __init__(self, scan_apk: ScanApk) -> None:
        self._scan_apk = scan_apk

    def handle(self, request: HttpRequest) -> HttpResponse:
        if is_cross_origin(request):
            return json_response(403, {"detail": "Cross-origin requests are not allowed."})
        try:
            length = int(request.header("content-length", ""))
        except ValueError:
            return json_response(411, {"detail": "Content-Length required."})
        try:
            report = self._scan_apk.execute(request.body, length)
        except ScanError as error:
            status, payload = present_error(error)
            return json_response(status, payload)
        return json_response(200, present_report(report))
