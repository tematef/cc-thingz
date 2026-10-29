import unittest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from billsched.dedup import ExecutionWindowGuard
from billsched.planner import BillingPlanner, SubscriptionRule

class RolloverDstTest(unittest.TestCase):
    def test_spring_dst_preserves_local_billing_time(self) -> None:
        tz = ZoneInfo('America/New_York')
        rule = SubscriptionRule('sub-1', 'America/New_York', 1, 30)
        before_dst = datetime(2026, 3, 8, 1, 30, tzinfo=tz).astimezone(timezone.utc)
        planner = BillingPlanner(ExecutionWindowGuard())
        after_dst = planner.schedule_next(rule, before_dst)
        self.assertIsNotNone(after_dst, 'Subscription run was skipped across spring DST transition')
