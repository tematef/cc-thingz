"""Unit tests for WebhookDispatcher."""

from __future__ import annotations

import unittest

from hookrelay import DeliveryResult, TransportError, WebhookDispatcher, WebhookEvent


class FakeSender:
    def __init__(self, responses: list[int | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, bytes, dict[str, str], float]] = []

    def send(
        self,
        url: str,
        body: bytes,
        headers: dict[str, str],
        timeout_s: float,
    ) -> int:
        self.calls.append((url, body, dict(headers), timeout_s))
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class WebhookDispatcherTest(unittest.TestCase):
    def test_successful_delivery(self) -> None:
        sender = FakeSender([202])
        dispatcher = WebhookDispatcher(sender, timeout_s=3.0)
        event = WebhookEvent(
            event_id="evt-1",
            target_url="https://example.test/hooks",
            payload={"order_id": 42},
        )
        res = dispatcher.deliver(event)
        self.assertEqual(
            res,
            DeliveryResult(
                event_id="evt-1",
                ok=True,
                status_code=202,
                attempts=1,
                error=None,
            ),
        )
        self.assertEqual(len(sender.calls), 1)
        self.assertEqual(sender.calls[0][2]["X-Webhook-Id"], "evt-1")

    def test_http_error_returns_failed_result(self) -> None:
        sender = FakeSender([503])
        dispatcher = WebhookDispatcher(sender)
        event = WebhookEvent(
            event_id="evt-2",
            target_url="https://example.test/hooks",
            payload={"order_id": 99},
        )
        res = dispatcher.deliver(event)
        self.assertFalse(res.ok)
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.attempts, 1)
        self.assertEqual(res.error, "HTTP 503")

    def test_transport_error_returns_failed_result(self) -> None:
        sender = FakeSender([TransportError("connection timed out")])
        dispatcher = WebhookDispatcher(sender)
        event = WebhookEvent(
            event_id="evt-3",
            target_url="https://example.test/hooks",
            payload={"order_id": 100},
        )
        res = dispatcher.deliver(event)
        self.assertFalse(res.ok)
        self.assertIsNone(res.status_code)
        self.assertEqual(res.attempts, 1)
        self.assertIn("timed out", res.error or "")


if __name__ == "__main__":
    unittest.main()
