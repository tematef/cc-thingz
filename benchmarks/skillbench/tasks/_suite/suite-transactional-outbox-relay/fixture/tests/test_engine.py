import unittest
from outboxrelay.engine import OrderStore

class EngineTest(unittest.TestCase):
    def test_create_order(self) -> None:
        store = OrderStore()
        o = store.create_order('ord-1', 1500)
        self.assertEqual(o.order_id, 'ord-1')
