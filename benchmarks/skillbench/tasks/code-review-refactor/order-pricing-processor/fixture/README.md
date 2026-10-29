# orderflow

`orderflow` validates e-commerce orders, computes bulk discounts, coupons, regional shipping, and tax, and formats text receipts.

## Layout

- `orderflow/processor.py` — `process_order`, `estimate_order`, and `format_receipt`.
- `tests/test_processor.py` — `unittest` suite (`python -m unittest discover -s tests -v`).
