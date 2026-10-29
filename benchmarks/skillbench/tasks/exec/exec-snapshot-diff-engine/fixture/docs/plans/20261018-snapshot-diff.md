# Plan: Recursive Snapshot Diff and Reversible Patch

### Task 1: Nested Dot-Path Diffing
- [ ] Update `diff_snapshots(before, after)` in `statecfg/differ.py` to recursively compare nested `dict` objects using dot-joined paths (`'a.b.c'`) while treating lists and scalars as atomic values, returning `list[ChangeEntry]` sorted by `path`.

### Task 2: Patch Application and Reversion
- [ ] Implement `apply_diff(snapshot, changes) -> dict` and `revert_diff(snapshot, changes) -> dict` that return new deep-copied dictionaries with changes applied or reverted (cleaning up empty parent dicts when nested keys are removed if created by the patch, or restoring previous state).
- [ ] Add unit tests in `tests/test_nested_diff.py` testing nested diffs, `apply_diff`, and `revert_diff`.
