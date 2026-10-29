"""Invoice ledger store with staged batch writes."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable


@dataclass(frozen=True)
class InvoiceRecord:
    invoice_id: str
    batch_id: str
    customer_id: str
    amount_cents: int
    status: str = "PENDING"
    tx_id: str | None = None


class LedgerStore:
    """Tracks invoice settlement state."""

    def __init__(self, records: Iterable[InvoiceRecord]) -> None:
        self._records: dict[str, InvoiceRecord] = {r.invoice_id: r for r in records}
        self._pending_writes: dict[str, InvoiceRecord] = {}

    def pending_for_batch(self, batch_id: str) -> list[InvoiceRecord]:
        """Return all committed PENDING invoices belonging to `batch_id`."""
        return [
            r
            for r in self._records.values()
            if r.batch_id == batch_id and r.status == "PENDING"
        ]

    def get(self, invoice_id: str) -> InvoiceRecord:
        return self._records[invoice_id]

    def mark_settled(self, invoice_id: str, tx_id: str) -> None:
        """Stage a SETTLED transition for `invoice_id` until `commit()` is called."""
        current = self._pending_writes.get(invoice_id) or self._records[invoice_id]
        self._pending_writes[invoice_id] = replace(
            current,
            status="SETTLED",
            tx_id=tx_id,
        )

    def commit(self) -> None:
        """Flush staged transitions to the committed ledger."""
        self._records.update(self._pending_writes)
        self._pending_writes.clear()

    def rollback(self) -> None:
        """Discard uncommitted staged transitions."""
        self._pending_writes.clear()
