from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class ScheduledJob:
    job_id: str
    priority: int = 0
    depends_on: frozenset[str] = frozenset()

class JobScheduler:
    def __init__(self) -> None:
        self._queue: list[ScheduledJob] = []
        self._completed: set[str] = set()
    def submit(self, job_id: str, priority: int = 0, depends_on: Iterable[str] = ()) -> ScheduledJob:
        job = ScheduledJob(job_id=job_id, priority=priority, depends_on=frozenset(depends_on))
        self._queue.append(job)
        return job
    def pop_ready(self) -> ScheduledJob | None:
        if not self._queue:
            return None
        return self._queue.pop(0)
