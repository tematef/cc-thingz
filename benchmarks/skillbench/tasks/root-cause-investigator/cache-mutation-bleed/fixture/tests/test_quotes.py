"""Unit tests for InvoiceBuilder quotes."""

from __future__ import annotations

import unittest

from quoteengine import InvoiceBuilder


class InvoiceQuoteTest(unittest.TestCase):
    def test_vip_promo_then_fresh_builder_for_standard_customer(self) -> None:
        vip_builder = InvoiceBuilder()
        vip_quote = vip_builder.build_quote(
            "cust-vip",
            "pro-seat",
            5,
            promo_code="VIP15",
        )
        self.assertEqual(vip_quote["unit_cents"], 1700)
        self.assertEqual(vip_quote["subtotal_cents"], 8500)
        self.assertEqual(vip_quote["applied_promo"], "VIP15")

        # A separate request uses a brand-new InvoiceBuilder with no promo code.
        standard_builder = InvoiceBuilder()
        standard_quote = standard_builder.build_quote(
            "cust-standard",
            "pro-seat",
            5,
            promo_code=None,
        )
        self.assertIsNone(standard_quote["applied_promo"])
        self.assertEqual(standard_quote["unit_cents"], 2000)
        self.assertEqual(standard_quote["subtotal_cents"], 10000)


if __name__ == "__main__":
    unittest.main()
