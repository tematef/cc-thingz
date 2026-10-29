"""Transport interface for HTTP webhook delivery."""

from __future__ import annotations

from typing import Protocol


class TransportError(RuntimeError):
    """Raised when an HTTP request times out or fails at the network layer."""


class HttpSender(Protocol):
    """Callable transport that posts a serialized webhook payload and returns an HTTP status."""

    def send(
        self,
        url: str,
        body: bytes,
        headers: dict[str, str],
        timeout_s: float,
    ) -> int: ...
