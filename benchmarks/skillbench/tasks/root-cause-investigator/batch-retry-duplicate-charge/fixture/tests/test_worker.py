"""Unit tests for BatchWorker settlement and retry."""

from __future__ import annotations

import unittest

from settleworker import (
    BatchWorker,
    GatewayTimeoutError,
    InvoiceRecord,
    LedgerStore,
    PaymentGateway,
)


class BatchWorkerTest(unittest.TestCase):
    def test_retry_after_mid_batch_timeout_does_not_double_charge(self) -> None:
        ledger = LedgerStore(
            [
                InvoiceRecord(
                    invoice_id="inv-101",
                    batch_id="batch-07",
                    customer_id="cust-alice",
                    amount_cents=5000,
                ),
                InvoiceRecord(
                    invoice_id="inv-102",
                    batch_id="batch-07",
                    customer_id="cust-bob",
                    amount_cents=7500,
                ),
            ]
        )
        gateway = PaymentGateway()
        gateway.fail_next_for_customer("cust-bob")
        worker = BatchWorker(ledger, gateway)

        with self.assertRaises(GatewayTimeoutError):
            worker.process_batch("batch-07")

        # Retry the batch after the transient timeout on cust-bob clears.
        worker.process_batch("batch-07")

        self.assertEqual(ledger.get("inv-101").status, "SETTLED")
        self.assertEqual(ledger.get("inv-102").status, "SETTLED")
        alice_charges = [c for c in gateway.charges if c.customer_id == "cust-alice"]
        self.assertEqual(
            len(alice_charges),
            1,
            f"expected cust-alice to be charged once, got {alice_charges}",
        )


if __name__ == "__main__":
    unittest.main()
