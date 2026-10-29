# Plan: Weighted Sliding-Window Quota Limiter

### Task 1: Sliding Window Timestamp Pruning and Weighted Cost
- [ ] Update `QuotaDecision` in `ratelimiter/quota.py` to include `remaining: int` and `retry_after_s: float`.
- [ ] Update `QuotaLimiter.check_and_consume(key: str, cost: int = 1) -> QuotaDecision` to prune entries with `timestamp <= now - window_s` before summing active cost.
- [ ] Reject with `allowed=False` without recording the event when `active_cost + cost > max_units`, computing `retry_after_s` as the time until the oldest events needed to free `(active_cost + cost - max_units)` units expire.

### Task 2: Unit Tests for Sliding Window and Retry-After
- [ ] Add unit tests in `tests/test_sliding_quota.py` using a controllable fake clock to test expiration, weighted costs, atomic rejection, and exact `retry_after_s` values.
