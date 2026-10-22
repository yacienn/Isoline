"""Tiny framework-free request/response types, so controllers are testable without sockets."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import BinaryIO, Mapping


@dataclass
class HttpRequest:
    method: str
    path: str
    headers: Mapping[str, str]          # keys lower-cased by the server adapter
    body: BinaryIO

    def header(self, name: str, default: str | None = None) -> str | None:
        return self.headers.get(name.lower(), default)


@dataclass
class HttpResponse:
    status: int
    body: bytes
    content_type: str
    headers: dict[str, str] = field(default_factory=dict)


def json_response(status: int, payload: dict) -> HttpResponse:
    return HttpResponse(status, json.dumps(payload).encode(), "application/json")
