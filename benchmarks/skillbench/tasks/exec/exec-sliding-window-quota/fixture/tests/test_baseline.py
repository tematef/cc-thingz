import unittest
from ratelimiter.quota import QuotaLimiter

class QuotaBaselineTest(unittest.TestCase):
    def test_allows_within_budget(self) -> None:
        limiter = QuotaLimiter(max_units=5, window_s=10.0, clock=lambda: 100.0)
        dec = limiter.check_and_consume('k1', cost=2)
        self.assertTrue(dec.allowed)
        self.assertEqual(dec.remaining, 3)
