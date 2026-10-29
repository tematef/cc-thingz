import unittest
from billengine.billing import InvoiceBuilder, UsageMeter

class BillingTest(unittest.TestCase):
    def test_close_period(self) -> None:
        m = UsageMeter()
        m.record('t1', '2026-10', 10)
        inv = InvoiceBuilder(m, unit_price_cents=5).close_billing_period('t1', '2026-10')
        self.assertEqual(inv.total_cents, 50)
