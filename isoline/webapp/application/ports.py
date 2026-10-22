"""Ports: what the use case needs from the outside world. Infrastructure implements them."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, ContextManager, Protocol


@dataclass(frozen=True)
class RawScan:
    """What a scanner returns: facts and a model score, no interpretation."""
    sha256: str
    malicious_score: float            # 0-1
    permission_names: tuple[str, ...]


class ApkScanner(Protocol):
    def scan(self, apk_path: Path) -> RawScan:
        """Raise a ScanError subclass on failure."""


class UploadStorage(Protocol):
    def store(self, stream: BinaryIO, length: int) -> ContextManager[Path]:
        """Persist exactly `length` bytes from `stream`; the file is removed when the block exits."""
