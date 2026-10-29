"""Authenticated request router."""

from __future__ import annotations

from typing import Callable, Iterable

from .request import Request, Response

RouteHandler = Callable[[Request], Response]


class Router:
    """Dispatches authenticated HTTP requests to registered route handlers."""

    def __init__(self, api_keys: Iterable[str]) -> None:
        self._api_keys: set[str] = {k for k in api_keys if k}
        self._routes: dict[tuple[str, str], RouteHandler] = {}

    def register(self, method: str, path: str, handler: RouteHandler) -> None:
        self._routes[(method.upper(), path)] = handler

    def handle(self, request: Request) -> Response:
        api_key = request.header("X-API-Key")
        if not api_key or api_key not in self._api_keys:
            return Response(status=401, body={"error": "unauthorized"})

        handler = self._routes.get((request.method.upper(), request.path))
        if handler is None:
            return Response(status=404, body={"error": "not found"})

        return handler(request)
