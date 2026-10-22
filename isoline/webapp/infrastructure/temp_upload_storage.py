from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Iterator

from ..application.errors import UploadIncomplete

CHUNK = 1 << 20  # 1 MiB


class TempUploadStorage:
    """Streams an upload to a temporary file (never into memory) and deletes it afterwards."""

    @contextmanager
    def store(self, stream: BinaryIO, length: int) -> Iterator[Path]:
        fd, name = tempfile.mkstemp(suffix=".apk")
        path = Path(name)
        try:
            with os.fdopen(fd, "wb") as out:
                remaining = length
                while remaining:
                    chunk = stream.read(min(CHUNK, remaining))
                    if not chunk:
                        raise UploadIncomplete("Upload was cut short.")
                    out.write(chunk)
                    remaining -= len(chunk)
            yield path
        finally:
            try:
                path.unlink()
            except OSError:
                pass
