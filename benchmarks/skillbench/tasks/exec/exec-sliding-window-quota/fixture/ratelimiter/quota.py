import time
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class QuotaDecision:
    allowed: bool
    remaining: int = 0
    retry_after_s: float = 0.0

class QuotaLimiter:
    def __init__(self, max_units: int, window_s: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.max_units = max_units
        self.window_s = window_s
        self._clock = clock
        self._events: dict[str, list[tuple[float, int]]] = {}
    def check_and_consume(self, key: str, cost: int = 1) -> QuotaDecision:
        now = self._clock()
        bucket = self._events.setdefault(key, [])
        used = sum(c for _, c in bucket)
        if used + cost > self.max_units:
            return QuotaDecision(allowed=False, remaining=max(0, self.max_units - used), retry_after_s=0.0)
        bucket.append((now, cost))
        return QuotaDecision(allowed=True, remaining=self.max_units - (used + cost), retry_after_s=0.0)
