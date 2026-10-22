from __future__ import annotations

from typing import BinaryIO

from ..domain.report import ScanReport, assess
from .errors import UploadRejected
from .ports import ApkScanner, UploadStorage


class ScanApk:
    """Use case: take an uploaded APK stream and return a verdict report."""

    def __init__(self, storage: UploadStorage, scanner: ApkScanner, max_bytes: int) -> None:
        self._storage = storage
        self._scanner = scanner
        self._max_bytes = max_bytes

    def execute(self, stream: BinaryIO, length: int) -> ScanReport:
        if length <= 0 or length > self._max_bytes:
            raise UploadRejected(f"File is empty or larger than {self._max_bytes // (1024 * 1024)} MB.")
        with self._storage.store(stream, length) as apk_path:
            raw = self._scanner.scan(apk_path)
        return assess(raw.sha256, raw.malicious_score, raw.permission_names)
