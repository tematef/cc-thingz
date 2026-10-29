"""Unit tests for Router."""

from __future__ import annotations

import unittest

from apigate import Request, Response, Router


class RouterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.router = Router(api_keys=["key-alpha", "key-beta"])
        self.router.register(
            "GET",
            "/v1/items",
            lambda req: Response(status=200, body={"items": ["a", "b"]}),
        )

    def test_authenticated_route_succeeds(self) -> None:
        resp = self.router.handle(
            Request(method="GET", path="/v1/items", headers={"X-API-Key": "key-alpha"})
        )
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.body, {"items": ["a", "b"]})

    def test_missing_or_invalid_api_key_returns_401(self) -> None:
        missing = self.router.handle(Request(method="GET", path="/v1/items"))
        self.assertEqual(missing.status, 401)
        invalid = self.router.handle(
            Request(method="GET", path="/v1/items", headers={"x-api-key": "unknown"})
        )
        self.assertEqual(invalid.status, 401)

    def test_unknown_route_returns_404(self) -> None:
        resp = self.router.handle(
            Request(method="POST", path="/v1/items", headers={"X-API-Key": "key-beta"})
        )
        self.assertEqual(resp.status, 404)


if __name__ == "__main__":
    unittest.main()
