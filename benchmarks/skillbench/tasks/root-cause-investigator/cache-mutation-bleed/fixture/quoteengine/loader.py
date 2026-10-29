"""Catalog loader with process-level memoization."""

from __future__ import annotations

from typing import Any

from .catalog import PricingCatalog

_DEFAULT_PLANS: dict[str, dict[str, Any]] = {
    "pro-seat": {
        "sku": "pro-seat",
        "currency": "USD",
        "tiers": [
            {"min_qty": 1, "unit_cents": 2000},
            {"min_qty": 25, "unit_cents": 1600},
        ],
    },
    "enterprise-seat": {
        "sku": "enterprise-seat",
        "currency": "USD",
        "tiers": [
            {"min_qty": 1, "unit_cents": 5000},
            {"min_qty": 50, "unit_cents": 4000},
        ],
    },
}

_CATALOG_CACHE: dict[str, PricingCatalog] = {}


def load_catalog(profile: str = "default") -> PricingCatalog:
    """Load the pricing catalog for `profile`, reusing the cached instance."""
    if profile not in _CATALOG_CACHE:
        raw = {
            sku: {
                "sku": data["sku"],
                "currency": data["currency"],
                "tiers": [dict(t) for t in data["tiers"]],
            }
            for sku, data in _DEFAULT_PLANS.items()
        }
        _CATALOG_CACHE[profile] = PricingCatalog(raw)
    return _CATALOG_CACHE[profile]
