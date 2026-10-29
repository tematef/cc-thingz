from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class Envelope:
    msg_id: str
    topic: str
    payload: str

class MessageBroker:
    def __init__(self, handler: Callable[[Envelope], None], max_attempts: int = 3) -> None:
        self._handler = handler
        self.max_attempts = max_attempts
        self.delivered_ids: set[str] = set()
    def dispatch(self, env: Envelope) -> bool:
        if env.msg_id in self.delivered_ids:
            return True
        for _ in range(self.max_attempts):
            try:
                self._handler(env)
                self.delivered_ids.add(env.msg_id)
                return True
            except Exception:
                continue
        return False
