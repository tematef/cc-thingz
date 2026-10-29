"""Promotional discount rules."""

from __future__ import annotations

from typing import Any

PROMO_DISCOUNTS_PCT: dict[str, int] = {
    "WELCOME10": 10,
    "VIP15": 15,
    "PARTNER25": 25,
}


def apply_promotion(plan: dict[str, Any], promo_code: str | None) -> dict[str, Any]:
    """Apply `promo_code` percentage discount to the tier prices in `plan`."""
    if not promo_code:
        return plan
    pct = PROMO_DISCOUNTS_PCT.get(promo_code.upper())
    if pct is None:
        raise ValueError(f"unknown promo code: {promo_code!r}")
    plan["applied_promo"] = promo_code.upper()
    for tier in plan["tiers"]:
        tier["unit_cents"] = int(tier["unit_cents"] * (100 - pct) // 100)
    return plan
