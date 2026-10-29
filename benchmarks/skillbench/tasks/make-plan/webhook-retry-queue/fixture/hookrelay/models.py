"""Data models for outbound webhook events and delivery outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WebhookEvent:
    """One outbound webhook event to deliver to `target_url`."""

    event_id: str
    target_url: str
    payload: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DeliveryResult:
    """Outcome of dispatching a `WebhookEvent`."""

    event_id: str
    ok: bool
    status_code: int | None
    attempts: int
    error: str | None = None
