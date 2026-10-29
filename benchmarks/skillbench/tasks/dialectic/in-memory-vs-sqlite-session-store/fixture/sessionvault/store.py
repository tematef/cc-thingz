import threading
from dataclasses import dataclass

@dataclass
class SessionToken:
    token_id: str
    user_id: str
    expires_at: float
    last_seen_at: float

class SessionStore:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._tokens: dict[str, SessionToken] = {}
    def put(self, tok: SessionToken) -> None:
        with self._lock:
            self._tokens[tok.token_id] = tok
    def validate_and_touch(self, token_id: str, now: float) -> SessionToken | None:
        with self._lock:
            tok = self._tokens.get(token_id)
            if tok is None or tok.expires_at <= now:
                return None
            tok.last_seen_at = now
            return tok
