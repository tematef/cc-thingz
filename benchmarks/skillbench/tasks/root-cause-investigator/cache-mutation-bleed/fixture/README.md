# quoteengine

`quoteengine` calculates multi-tier subscription quotes with promotional discounts and regional tax.

## Layout

- `quoteengine/catalog.py` — `PricingCatalog` holding SKU tier tables.
- `quoteengine/loader.py` — `load_catalog()` loader with in-memory catalog memoization.
- `quoteengine/promotions.py` — `apply_promotion()` for promotional discount codes.
- `quoteengine/billing.py` — `InvoiceBuilder` that produces quote summaries for customers.
- `tests/test_quotes.py` — `unittest` suite (`python -m unittest discover -s tests -v`).
