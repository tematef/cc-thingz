import unittest
from gatekeeper.router import RequestRouter, TenantPolicy

class RouterTest(unittest.TestCase):
    def test_basic_acquire_release(self) -> None:
        r = RequestRouter(max_inflight=2)
        r.register(TenantPolicy('t1', rpm_limit=10))
        self.assertTrue(r.acquire('t1').accepted)
        r.release('t1')
