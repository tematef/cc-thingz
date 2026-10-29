import unittest
from taxrecon.reconciler import compute_domestic_invoice, compute_export_invoice, format_tax_line

class TaxReconcilerTest(unittest.TestCase):
    def test_domestic_ca(self) -> None:
        res = compute_domestic_invoice([{'qty': 2, 'unit_cents': 6000}], 'CA')
        self.assertEqual(res['subtotal'], 12000)
        self.assertEqual(res['discount'], 600)
        self.assertEqual(res['tax'], 940)
        self.assertEqual(res['fee'], 0)
        self.assertEqual(res['total'], 12340)
    def test_export_gb(self) -> None:
        res = compute_export_invoice([{'qty': 1, 'unit_cents': 3000}], 'GB')
        self.assertEqual(res['total'], 4100)
        self.assertIn('GB: subtotal=3000', format_tax_line(res))
