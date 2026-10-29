import unittest
from auditlog.logger import AuditLogger

class AuditBaselineTest(unittest.TestCase):
    def test_record_and_list(self) -> None:
        log = AuditLogger()
        e = log.record('alice', 'login', {'ip': '10.0.0.1'})
        self.assertEqual(e.actor, 'alice')
        self.assertEqual(len(log.entries()), 1)
