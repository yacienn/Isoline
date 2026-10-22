"""Composition root: the only module that knows every layer and wires them together."""
from __future__ import annotations

from .application.scan_apk import ScanApk
from .config import Settings
from .infrastructure.subprocess_scanner import SubprocessApkScanner
from .infrastructure.temp_upload_storage import TempUploadStorage
from .interface.scan_controller import ScanController
from .interface.static_files import StaticFiles
from .interface.web_app import WebApp


def build_app(settings: Settings) -> WebApp:
    scanner = SubprocessApkScanner(settings.model_path, settings.project_root,
                                   settings.scan_timeout_s, settings.max_concurrent_scans)
    scan_apk = ScanApk(TempUploadStorage(), scanner, settings.max_upload_bytes)
    return WebApp(ScanController(scan_apk), StaticFiles(settings.static_dir))
