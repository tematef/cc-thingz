from dataclasses import dataclass

@dataclass
class LedgerEntry:
    entry_id: str
    account_id: str
    delta_cents: int

class EventSink:
    def __init__(self) -> None:
        self.published: list[LedgerEntry] = []
    def publish(self, entry: LedgerEntry) -> None:
        self.published.append(entry)

class LedgerService:
    def __init__(self, sink: EventSink) -> None:
        self.balances: dict[str, int] = {}
        self.sink = sink
    def record_entry(self, entry: LedgerEntry) -> int:
        new_bal = self.balances.get(entry.account_id, 0) + entry.delta_cents
        self.balances[entry.account_id] = new_bal
        self.sink.publish(entry)
        return new_bal
