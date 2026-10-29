# settleworker

`settleworker` settles batches of pending customer invoices against an external payment gateway.

## Layout

- `settleworker/gateway.py` — `PaymentGateway` with idempotency-key deduplication and `GatewayTimeoutError`.
- `settleworker/ledger.py` — `InvoiceRecord` and `LedgerStore` tracking pending vs settled invoices.
- `settleworker/worker.py` — `BatchWorker` driving batch settlement and retry.
- `tests/test_worker.py` — `unittest` suite (`python -m unittest discover -s tests -v`).
