from datetime import datetime

class ExecutionWindowGuard:
    def __init__(self) -> None:
        self._seen: set[str] = set()
    def should_run(self, sub_id: str, dt_utc: datetime, expected_utc_hour: int) -> bool:
        if dt_utc.hour != expected_utc_hour:
            return False
        key = f"{sub_id}:{dt_utc.strftime('%Y-%m-%d:%H')}"
        if key in self._seen:
            return False
        self._seen.add(key)
        return True
