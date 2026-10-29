import unittest
from dlqbroker.broker import Envelope, MessageBroker

class BrokerTest(unittest.TestCase):
    def test_dispatch_success(self) -> None:
        seen = []
        b = MessageBroker(lambda e: seen.append(e.msg_id))
        self.assertTrue(b.dispatch(Envelope('m1', 'orders', 'body')))
        self.assertEqual(seen, ['m1'])
