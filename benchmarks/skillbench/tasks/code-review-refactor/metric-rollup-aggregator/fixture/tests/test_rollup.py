import unittest
from telemetryrollup.rollup import render_badge, summarize_error_samples, summarize_latency_samples

class RollupTest(unittest.TestCase):
    def test_latency_warn(self) -> None:
        rep = summarize_latency_samples('api', [50.0, -1.0, 120.0, 260.0])
        self.assertEqual(rep['count'], 3)
        self.assertEqual(rep['status'], 'WARN')
        self.assertEqual(render_badge(rep), '[WARN] api (n=3, p95=260.0)')
    def test_error_critical(self) -> None:
        rep = summarize_error_samples('auth', [0.2, 6.5])
        self.assertEqual(rep['status'], 'CRITICAL')
