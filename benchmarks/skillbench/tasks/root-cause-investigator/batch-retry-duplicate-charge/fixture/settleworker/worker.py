"""Batch settlement worker."""

from __future__ import annotations

import hashlib

from .gateway import GatewayTimeoutError, PaymentGateway
from .ledger import InvoiceRecord, LedgerStore


class BatchWorker:
    """Charges all pending invoices in a batch and updates the ledger."""

    def __init__(self, ledger: LedgerStore, gateway: PaymentGateway) -> None:
        self._ledger = ledger
        self._gateway = gateway
        self._attempt_seq = 0

    def _build_idempotency_key(self, record: InvoiceRecord, attempt: int) -> str:
        raw = f"{record.batch_id}:{record.invoice_id}:attempt={attempt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def process_batch(self, batch_id: str) -> list[str]:
        """Charge every pending invoice in `batch_id` and return settled invoice IDs."""
        self._attempt_seq += 1
        attempt = self._attempt_seq
        pending = self._ledger.pending_for_batch(batch_id)
        settled_ids: list[str] = []
        try:
            for record in pending:
                idem_key = self._build_idempotency_key(record, attempt)
                receipt = self._gateway.charge(
                    record.customer_id,
                    record.amount_cents,
                    idempotency_key=idem_key,
                )
                self._ledger.mark_settled(record.invoice_id, receipt.tx_id)
                settled_ids.append(record.invoice_id)
        except GatewayTimeoutError:
            self._ledger.rollback()
            raise
        self._ledger.commit()
        return settled_ids
