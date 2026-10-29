from dataclasses import dataclass
from typing import Any

@dataclass
class AuditEntry:
    actor: str
    action: str
    details: dict[str, Any]
    prev_hash: str = 'GENESIS'
    entry_hash: str = ''

class AuditLogger:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
    def record(self, actor: str, action: str, details: dict[str, Any]) -> AuditEntry:
        entry = AuditEntry(actor=actor, action=action, details=dict(details))
        self._entries.append(entry)
        return entry
    def entries(self) -> list[AuditEntry]:
        return list(self._entries)
