# hookrelay

`hookrelay` is a small Python library that dispatches outbound JSON webhooks to subscriber endpoints.

## Layout

- `hookrelay/models.py` — `WebhookEvent` and `DeliveryResult` dataclasses.
- `hookrelay/transport.py` — `HttpSender` protocol and `TransportError` exception.
- `hookrelay/dispatcher.py` — `WebhookDispatcher`, which currently sends each event once with no retry or dead-letter handling.
- `tests/test_dispatcher.py` — `unittest` suite (`python -m unittest discover -s tests -v`).
