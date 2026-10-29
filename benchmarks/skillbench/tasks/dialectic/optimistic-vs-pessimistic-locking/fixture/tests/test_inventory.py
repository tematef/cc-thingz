import unittest
from stocklock.inventory import InventoryTable

class InventoryTest(unittest.TestCase):
    def test_reserve(self) -> None:
        inv = InventoryTable()
        inv.seed('sku-a', 5)
        self.assertTrue(inv.reserve_items({'sku-a': 3}))
        self.assertFalse(inv.reserve_items({'sku-a': 3}))
