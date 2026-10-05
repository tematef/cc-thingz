---
worth: yes
where: tests/test-exec-vcs-dispatch.sh
added: 2026-10-05
---
# dispatch suite fails when the caller exports CODEX_MODEL or CODEX_NO_OVERRIDES

The suite never clears `CODEX_MODEL` or `CODEX_NO_OVERRIDES` before the `run-codex.sh` cases that assume
them unset, so both leak in from the caller's shell. `CODEX_MODEL=gpt-9 bash tests/test-exec-vcs-dispatch.sh`
fails the "no -c model= when CODEX_MODEL unset" assertions (tests 15 and 16), and `CODEX_NO_OVERRIDES=1`
fails the effort, idle-timeout and `CODEX_MODEL` override assertions. CI is unaffected because the runner
sets neither. Fix: `unset CODEX_MODEL CODEX_NO_OVERRIDES` at the top of the suite; the cases that need a
value already set it per invocation.

Related gap in the same block: test 15c runs with `CODEX_MODEL` unset, so its "no -c model= when
CODEX_NO_OVERRIDES=1" assertion passes whether or not the guard suppresses the model flag. Setting
`CODEX_MODEL=gpt-5.6` on that invocation makes it able to fail.
