# Plan: Priority and Dependency Job Scheduler

### Task 1: Priority Ordering and Dependency Gating
- [ ] In `jobqueue/scheduler.py`, extend `JobScheduler.submit(job_id, priority=0, depends_on=())` to store `depends_on: frozenset[str]` and monotonic submission order.
- [ ] Update `pop_ready() -> ScheduledJob | None` to only consider non-cancelled jobs whose `depends_on` IDs are all in `self._completed`, returning the one with highest `priority` (and lowest submission sequence on ties).
- [ ] Add `mark_completed(job_id: str) -> None` and `cancel(job_id: str) -> bool`.

### Task 2: Comprehensive Scheduler Unit Tests
- [ ] Add tests in `tests/test_priority_deps.py` covering priority ordering, FIFO tie-breaks, blocked jobs becoming ready after `mark_completed`, and `cancel`.
