"""APK -> permission vector (Phase 2 deliverable)."""
from __future__ import annotations

import zipfile
from pathlib import Path

from .schema import FEATURE_PERMISSIONS

MAX_APK_BYTES = 150 * 1024 * 1024  # refuse absurdly large inputs


class InvalidAPKError(ValueError):
    pass


def validate_apk_file(path: str | Path) -> Path:
    """Cheap sanity checks BEFORE handing an untrusted file to a parser."""
    path = Path(path).resolve()
    if not path.is_file():
        raise InvalidAPKError(f"Not a file: {path}")
    size = path.stat().st_size
    if size == 0 or size > MAX_APK_BYTES:
        raise InvalidAPKError(f"Unacceptable file size: {size} bytes")
    if not zipfile.is_zipfile(path):
        raise InvalidAPKError("Not a ZIP/APK container")
    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
    if "AndroidManifest.xml" not in names:
        raise InvalidAPKError("AndroidManifest.xml missing")
    return path


def extract_permissions(apk_path: str | Path) -> list[str]:
    """Declared permissions only (static; the APK is never executed)."""
    path = validate_apk_file(apk_path)  # validate BEFORE parsing
    try:  # Androguard logs every step at DEBUG; keep only warnings
        import sys
        from loguru import logger
        logger.remove()
        logger.add(sys.stderr, level="WARNING")
    except ImportError:
        pass
    from androguard.core.apk import APK  # lazy: heavy import
    try:
        apk = APK(str(path))
        return sorted(set(apk.get_permissions()))
    except Exception as exc:  # parser errors on malformed/hostile files
        raise InvalidAPKError(f"Could not parse APK: {exc}") from exc


def permissions_to_vector(permissions: list[str],
                          feature_names: list[str] | None = None) -> list[int]:
    """Binary vector in the order of feature_names (defaults to the built-in schema)."""
    names = FEATURE_PERMISSIONS if feature_names is None else feature_names
    declared = set(permissions)
    return [1 if p in declared else 0 for p in names]


def extract_vector(apk_path: str | Path) -> list[int]:
    return permissions_to_vector(extract_permissions(apk_path))
