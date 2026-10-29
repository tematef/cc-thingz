"""Invoice quote builder."""

from __future__ import annotations

from typing import Any

from .catalog import PricingCatalog
from .loader import load_catalog
from .promotions import apply_promotion


def _select_unit_cents(tiers: list[dict[str, int]], qty: int) -> int:
    eligible = [t["unit_cents"] for t in tiers if qty >= t["min_qty"]]
    if not eligible:
        raise ValueError(f"no pricing tier matches quantity {qty}")
    return min(eligible)


class InvoiceBuilder:
    """Builds customer price quotes from a `PricingCatalog`."""

    def __init__(self, catalog: PricingCatalog | None = None) -> None:
        self._catalog = catalog if catalog is not None else load_catalog()

    def build_quote(
        self,
        customer_id: str,
        sku: str,
        qty: int,
        *,
        promo_code: str | None = None,
        tax_rate_bps: int = 800,
    ) -> dict[str, Any]:
        if qty <= 0:
            raise ValueError("qty must be positive")
        plan = self._catalog.get_plan(sku)
        effective_plan = apply_promotion(plan, promo_code)
        unit_cents = _select_unit_cents(effective_plan["tiers"], qty)
        subtotal_cents = unit_cents * qty
        tax_cents = (subtotal_cents * tax_rate_bps) // 10_000
        return {
            "customer_id": customer_id,
            "sku": sku,
            "qty": qty,
            "unit_cents": unit_cents,
            "subtotal_cents": subtotal_cents,
            "tax_cents": tax_cents,
            "total_cents": subtotal_cents + tax_cents,
            "applied_promo": effective_plan.get("applied_promo"),
        }
