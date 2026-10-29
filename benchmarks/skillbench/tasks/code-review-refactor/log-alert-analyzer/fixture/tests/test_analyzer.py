"""Unit tests for logwatch.analyzer."""

from __future__ import annotations

import unittest

from logwatch import (
    analyze_log_lines,
    filter_critical_events,
    render_markdown_summary,
)

SAMPLE_LOGS = [
    "# comment line",
    "   ",
    "2026-10-23T10:00:01Z service=auth level=INFO latency_ms=40 status=200 msg=ok",
    "2026-10-23T10:00:02Z service=auth level=WARN latency_ms=120 status=200 msg=slow",
    "2026-10-23T10:00:03Z service=billing level=ERR latency_ms=300 status=502 msg=bad_gateway",
    "2026-10-23T10:00:04Z service=billing level=CRIT latency_ms=500 status=503 msg=unavailable",
    "2026-10-23T10:00:05Z service=billing level=INFO latency_ms=100 status=200 msg=recovered",
    "2026-10-23T10:00:06Z service=search level=INFO latency_ms=1250 status=200 msg=heavy_query",
    "malformed_line_without_kv",
    "2026-10-23T10:00:07Z service=auth level=UNKNOWN latency_ms=10 status=200",
    "2026-10-23T10:00:08Z service=auth level=INFO latency_ms=notanint status=200",
]


class LogAnalyzerTest(unittest.TestCase):
    def test_analyze_log_lines_aggregates_and_classifies_health(self) -> None:
        rep = analyze_log_lines(SAMPLE_LOGS)
        self.assertEqual(rep["valid_events"], 6)
        self.assertEqual(rep["malformed_lines"], 3)
        self.assertEqual(set(rep["services"]), {"auth", "billing", "search"})

        auth = rep["services"]["auth"]
        self.assertEqual(auth["total_events"], 2)
        self.assertEqual(auth["error_events"], 0)
        self.assertEqual(auth["avg_latency_ms"], 80)
        self.assertEqual(auth["max_latency_ms"], 120)
        self.assertEqual(auth["health"], "healthy")

        billing = rep["services"]["billing"]
        self.assertEqual(billing["total_events"], 3)
        self.assertEqual(billing["error_events"], 2)
        self.assertEqual(billing["http_5xx_count"], 2)
        self.assertAlmostEqual(billing["error_rate"], 0.6667)
        self.assertEqual(billing["health"], "critical")

        search = rep["services"]["search"]
        self.assertEqual(search["total_events"], 1)
        self.assertEqual(search["max_latency_ms"], 1250)
        self.assertEqual(search["health"], "warning")

    def test_filter_critical_events(self) -> None:
        crit = filter_critical_events(SAMPLE_LOGS)
        self.assertEqual(len(crit), 3)
        self.assertEqual([c["service"] for c in crit], ["billing", "billing", "search"])
        self.assertEqual(crit[0]["level"], "ERROR")
        self.assertEqual(crit[1]["level"], "CRITICAL")
        self.assertEqual(crit[2]["latency_ms"], 1250)

    def test_render_markdown_summary(self) -> None:
        rep = analyze_log_lines(SAMPLE_LOGS)
        md = render_markdown_summary(rep)
        self.assertIn("Valid events: 6 | Malformed: 3", md)
        self.assertIn("- auth: HEALTHY (events=2, errors=0, max_latency=120ms)", md)
        self.assertIn("- billing: CRITICAL (events=3, errors=2, max_latency=500ms)", md)
        self.assertIn("- search: WARNING (events=1, errors=0, max_latency=1250ms)", md)


if __name__ == "__main__":
    unittest.main()
