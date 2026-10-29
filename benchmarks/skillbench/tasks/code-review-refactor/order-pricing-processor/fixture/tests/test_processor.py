"""Unit tests for orderflow.processor."""

from __future__ import annotations

import unittest

from orderflow import estimate_order, format_receipt, process_order


class OrderProcessorTest(unittest.TestCase):
    def test_standard_us_order_with_shipping_and_tax(self) -> None:
        order = {
            "customer": "Alice",
            "region": "US-CA",
            "items": [{"name": "Widget", "qty": 2, "unit_cents": 2000}],
        }
        res = process_order(order)
        self.assertEqual(res["status"], "CONFIRMED")
        self.assertEqual(res["subtotal_cents"], 4000)
        self.assertEqual(res["discount_cents"], 0)
        self.assertEqual(res["shipping_cents"], 799)
        self.assertEqual(res["tax_cents"], 330)
        self.assertEqual(res["total_cents"], 5129)

        est = estimate_order(order)
        self.assertEqual(
            est,
            {
                "subtotal_cents": 4000,
                "discount_cents": 0,
                "shipping_cents": 799,
                "tax_cents": 330,
                "total_cents": 5129,
            },
        )

    def test_bulk_discounts_and_coupons_and_free_shipping(self) -> None:
        order = {
            "customer": "Bob",
            "region": "EU",
            "coupon": "vip20",
            "items": [
                {"name": "Bolt", "qty": 50, "unit_cents": 500},
                {"name": "Nut", "qty": 20, "unit_cents": 200},
                {"name": "Washer", "qty": 10, "unit_cents": 100},
            ],
        }
        res = process_order(order)
        # Bolt: 500 * 85% = 425 * 50 = 21250
        # Nut: 200 * 90% = 180 * 20 = 3600
        # Washer: 100 * 95% = 95 * 10 = 950
        # Subtotal = 25800; VIP20 = 5160 -> after_disc = 20640 (>= 20000 so EU shipping = 0)
        # EU tax = 20% of 20640 = 4128; total = 24768
        self.assertEqual(res["subtotal_cents"], 25800)
        self.assertEqual(res["discount_cents"], 5160)
        self.assertEqual(res["shipping_cents"], 0)
        self.assertEqual(res["tax_cents"], 4128)
        self.assertEqual(res["total_cents"], 24768)
        self.assertEqual(estimate_order(order)["total_cents"], 24768)

    def test_flat_coupon_capped_at_subtotal_and_zero_tax_region(self) -> None:
        order = {
            "customer": "Carol",
            "region": "US-OR",
            "coupon": "FLAT500",
            "items": [{"name": "Pin", "qty": 1, "unit_cents": 300}],
        }
        res = process_order(order)
        self.assertEqual(res["subtotal_cents"], 300)
        self.assertEqual(res["discount_cents"], 300)
        self.assertEqual(res["shipping_cents"], 799)
        self.assertEqual(res["tax_cents"], 0)
        self.assertEqual(res["total_cents"], 799)

    def test_format_receipt(self) -> None:
        res = process_order(
            {
                "customer": "Alice",
                "region": "CA",
                "coupon": "SAVE10",
                "items": [{"name": "Book", "qty": 1, "unit_cents": 2000}],
            }
        )
        receipt = format_receipt(res)
        self.assertIn("Receipt for Alice (CA)", receipt)
        self.assertIn("- Book x1: 2000c", receipt)
        self.assertIn("Total: 3333c", receipt)

    def test_validation_errors(self) -> None:
        bad_orders = [
            {},
            {"customer": "Alice", "items": []},
            {
                "customer": "Alice",
                "region": "MARS",
                "items": [{"name": "X", "qty": 1, "unit_cents": 10}],
            },
            {
                "customer": "Alice",
                "items": [{"name": "", "qty": 1, "unit_cents": 10}],
            },
            {
                "customer": "Alice",
                "items": [{"name": "X", "qty": 0, "unit_cents": 10}],
            },
            {
                "customer": "Alice",
                "coupon": "NOPE",
                "items": [{"name": "X", "qty": 1, "unit_cents": 10}],
            },
        ]
        for bad in bad_orders:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    process_order(bad)
                with self.assertRaises(ValueError):
                    estimate_order(bad)


if __name__ == "__main__":
    unittest.main()
