"""SKU pricing catalog."""

from __future__ import annotations

from typing import Any


class PricingCatalog:
    """In-memory lookup of pricing plans keyed by SKU."""

    def __init__(self, plans: dict[str, dict[str, Any]]) -> None:
        self._plans = plans

    def get_plan(self, sku: str) -> dict[str, Any]:
        """Return a copy of the plan for `sku` so callers can customize it."""
        if sku not in self._plans:
            raise KeyError(f"unknown SKU: {sku!r}")
        entry = self._plans[sku]
        # Copy the plan dictionary so caller adjustments do not alter the catalog.
        return dict(entry)
