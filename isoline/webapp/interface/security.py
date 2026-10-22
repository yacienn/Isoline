from __future__ import annotations

from urllib.parse import urlparse

from .http_types import HttpRequest

# Sent on every response. The page only needs its own files, Google Fonts, and data: icons.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    ),
}


def is_cross_origin(request: HttpRequest) -> bool:
    """Block other websites from driving this local server."""
    origin = request.header("origin")
    return bool(origin) and urlparse(origin).netloc != request.header("host")
