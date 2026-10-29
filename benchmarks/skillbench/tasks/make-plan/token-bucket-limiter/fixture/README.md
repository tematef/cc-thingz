# apigate

`apigate` is a lightweight in-process HTTP request router with API-key authentication.

## Layout

- `apigate/request.py` — `Request` and `Response` value objects.
- `apigate/router.py` — `Router`, which validates `X-API-Key` headers and dispatches to registered route handlers.
- `tests/test_router.py` — `unittest` suite (`python -m unittest discover -s tests -v`).
