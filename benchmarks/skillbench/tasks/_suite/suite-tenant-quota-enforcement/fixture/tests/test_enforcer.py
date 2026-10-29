import unittest
from tenantquota.enforcer import QuotaEnforcer

class EnforcerTest(unittest.TestCase):
    def test_project_acquire(self) -> None:
        e = QuotaEnforcer()
        e.set_org_limit('org-1', 100)
        e.register_project('p-1', 'org-1', 10)
        self.assertTrue(e.acquire('p-1', 5))
