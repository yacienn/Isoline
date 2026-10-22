from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote

from .http_types import HttpResponse

_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",   # ES modules need a JavaScript MIME type
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


class StaticFiles:
    """Serves the front-end folder. Only known file types, never outside the root, no dotfiles."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def get(self, url_path: str) -> HttpResponse | None:
        relative = unquote(url_path).lstrip("/") or "index.html"
        try:
            candidate = (self._root / relative).resolve()
            inside = candidate.is_relative_to(self._root)
            is_file = inside and candidate.is_file()
        except (ValueError, OSError):  # e.g. NUL byte in the path
            return None
        if not is_file or candidate.suffix.lower() not in _TYPES:
            return None
        if any(part.startswith(".") for part in candidate.relative_to(self._root).parts):
            return None
        return HttpResponse(200, candidate.read_bytes(), _TYPES[candidate.suffix.lower()])
