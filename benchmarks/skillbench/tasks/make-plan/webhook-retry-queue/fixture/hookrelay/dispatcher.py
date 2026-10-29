"""Single-shot outbound webhook dispatcher."""

from __future__ import annotations

import json

from .models import DeliveryResult, WebhookEvent
from .transport import HttpSender, TransportError


class WebhookDispatcher:
    """Dispatches `WebhookEvent` instances over an `HttpSender`."""

    def __init__(self, sender: HttpSender, *, timeout_s: float = 5.0) -> None:
        self._sender = sender
        self._timeout_s = timeout_s

    def deliver(self, event: WebhookEvent) -> DeliveryResult:
        """Serialize `event` and send it once to `event.target_url`."""
        body = json.dumps(event.payload, sort_keys=True).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Id": event.event_id,
            **event.headers,
        }
        try:
            status = self._sender.send(
                event.target_url,
                body,
                headers,
                self._timeout_s,
            )
        except TransportError as exc:
            return DeliveryResult(
                event_id=event.event_id,
                ok=False,
                status_code=None,
                attempts=1,
                error=str(exc),
            )
        ok = 200 <= status < 300
        return DeliveryResult(
            event_id=event.event_id,
            ok=ok,
            status_code=status,
            attempts=1,
            error=None if ok else f"HTTP {status}",
        )
