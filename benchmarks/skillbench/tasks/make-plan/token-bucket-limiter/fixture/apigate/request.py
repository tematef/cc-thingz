"""HTTP Request and Response data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Request:
    """Incoming HTTP request."""

    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] | None = None

    def header(self, name: str) -> str | None:
        target = name.lower()
        for k, v in self.headers.items():
            if k.lower() == target:
                return v
        return None


@dataclass(frozen=True)
class Response:
    """Outgoing HTTP response."""

    status: int
    body: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
