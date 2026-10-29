import unittest
from ledgerbus.service import EventSink, LedgerEntry, LedgerService

class LedgerServiceTest(unittest.TestCase):
    def test_record_entry(self) -> None:
        sink = EventSink()
        svc = LedgerService(sink)
        self.assertEqual(svc.record_entry(LedgerEntry('e1', 'acc1', 250)), 250)
        self.assertEqual(len(sink.published), 1)
