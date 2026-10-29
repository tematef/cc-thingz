# Plan: Audit Redaction and Hash Chaining

### Task 1: Recursive Sensitive Field Redaction
- [ ] In `auditlog/logger.py`, add `redact_payload(data)` that deep-copies and replaces values of keys matching `{'password', 'secret', 'api_key', 'token', 'authorization'}` (case-insensitive) with `'[REDACTED]'` across nested dicts and lists.
- [ ] Update `AuditLogger.record(actor, action, details)` to store the redacted payload without mutating the caller's dictionary.

### Task 2: SHA-256 Hash Chain and Integrity Check
- [ ] Add `prev_hash: str` and `entry_hash: str` fields to `AuditEntry` (first entry uses `prev_hash='GENESIS'`).
- [ ] Compute `entry_hash` as the hex SHA-256 digest of `f"{prev_hash}|{actor}|{action}|{json.dumps(redacted_details, sort_keys=True)}"`.
- [ ] Implement `AuditLogger.verify_chain() -> bool` returning `True` when all `prev_hash` and `entry_hash` links are valid and `False` if any entry is modified.
- [ ] Add unit tests in `tests/test_redaction_and_chain.py` covering nested redaction, caller dict immutability, and tamper detection.
