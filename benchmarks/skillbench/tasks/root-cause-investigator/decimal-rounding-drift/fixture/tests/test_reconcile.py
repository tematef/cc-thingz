import unittest
from finsplit.reconciler import Reconciler

class ReconcileTest(unittest.TestCase):
    def test_three_way_split_with_discount_balances_to_cent(self) -> None:
        rec = Reconciler()
        summary = rec.verify_invoice(1000, 15.0, {'eng': 1, 'ops': 1, 'sales': 1})
        self.assertTrue(
            summary.balanced,
            f'Expected balanced invoice: net={summary.net_total_cents}, allocated={summary.allocated_sum_cents}',
        )
