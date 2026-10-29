from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from .dedup import ExecutionWindowGuard

@dataclass(frozen=True)
class SubscriptionRule:
    sub_id: str
    tz_name: str
    local_hour: int
    local_minute: int

class BillingPlanner:
    def __init__(self, guard: ExecutionWindowGuard) -> None:
        self.guard = guard
    def next_run_utc(self, rule: SubscriptionRule, last_utc: datetime) -> datetime:
        candidate_utc = last_utc + timedelta(hours=24)
        return candidate_utc.astimezone(timezone.utc)
    def schedule_next(self, rule: SubscriptionRule, last_utc: datetime) -> datetime | None:
        tz = ZoneInfo(rule.tz_name)
        initial_utc_hour = last_utc.astimezone(timezone.utc).hour
        nxt = self.next_run_utc(rule, last_utc)
        nxt_local = nxt.astimezone(tz)
        if (nxt_local.hour, nxt_local.minute) != (rule.local_hour, rule.local_minute):
            return None
        if not self.guard.should_run(rule.sub_id, nxt, initial_utc_hour):
            return None
        return nxt
