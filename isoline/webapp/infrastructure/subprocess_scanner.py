"""Scans an APK by running `python -m isoline.scan` in a SEPARATE process with a timeout.

APK parsing handles untrusted files, so it is isolated from the web server process.
The APK is never executed. At most `max_concurrent` scans run at once.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

from ..application.errors import InvalidApk, ModelNotTrained, ScannerFailure, ScanTimeout
from ..application.ports import RawScan


class SubprocessApkScanner:
    def __init__(self, model_path: Path, project_root: Path,
                 timeout_s: int = 90, max_concurrent: int = 2) -> None:
        self._model = model_path
        self._cwd = project_root
        self._timeout = timeout_s
        self._slots = threading.Semaphore(max_concurrent)

    def scan(self, apk_path: Path) -> RawScan:
        if not self._model.is_file():
            raise ModelNotTrained("No trained model found. Run: python -m isoline.train ...")
        with self._slots:
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "isoline.scan", str(apk_path), "--model", str(self._model)],
                    capture_output=True, text=True, timeout=self._timeout, cwd=self._cwd)
            except subprocess.TimeoutExpired as exc:
                raise ScanTimeout("Analysis timed out. The file may be malformed.") from exc
        try:
            result = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise ScannerFailure("The scanner crashed on this file.") from exc
        if result.get("status") != "ok":
            raise InvalidApk("Not a valid APK: " + str(result.get("error", "unknown error")))
        return RawScan(
            sha256=result["sha256"],
            malicious_score=float(result["malicious_score"]),
            permission_names=tuple(result["permissions"]),
        )
