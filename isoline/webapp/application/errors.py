"""Failures a scan can end in. Each one is a business outcome, not an HTTP status."""
from __future__ import annotations


class ScanError(Exception):
    """Base class; `message` is safe to show to the person using the site."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UploadRejected(ScanError):
    """Empty file or over the size limit."""


class UploadIncomplete(ScanError):
    """The connection ended before all bytes arrived."""


class ModelNotTrained(ScanError):
    """No trained model on disk yet."""


class InvalidApk(ScanError):
    """The file is not a parsable APK."""


class ScanTimeout(ScanError):
    """Parsing took too long (malformed or hostile file)."""


class ScannerFailure(ScanError):
    """The scanner process crashed or returned garbage."""
