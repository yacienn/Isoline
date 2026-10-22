"""Domain/application objects -> JSON the browser understands."""
from __future__ import annotations

from ..application.errors import (InvalidApk, ModelNotTrained, ScanError, ScannerFailure,
                                  ScanTimeout, UploadIncomplete, UploadRejected)
from ..domain.report import ScanReport

_STATUS_BY_ERROR: tuple[tuple[type[ScanError], int], ...] = (
    (UploadRejected, 413),
    (UploadIncomplete, 400),
    (ModelNotTrained, 503),
    (InvalidApk, 422),
    (ScanTimeout, 422),
    (ScannerFailure, 500),
)


def present_report(report: ScanReport) -> dict:
    return {
        "score": report.score_percent,
        "verdict": report.verdict.value,
        "sha256": report.sha256,
        "permission_count": report.permission_count,
        "permissions": [{"name": p.name, "risk": p.risk.value} for p in report.permissions],
        "indicators": [{"title": i.title, "detail": i.detail, "severity": i.severity.value}
                       for i in report.indicators],
    }


def present_error(error: ScanError) -> tuple[int, dict]:
    status = next((code for kind, code in _STATUS_BY_ERROR if isinstance(error, kind)), 500)
    return status, {"detail": error.message}
