#!/bin/bash
# automated tests for plugins/skill-eval/skill-forced-eval-hook.sh
# pins that the skill-activation instruction is injected once per turn
# (first model call of an executionId), not before every model call, and
# that the hook falls back to injecting whenever it cannot tell turns apart

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HOOK="$REPO_ROOT/plugins/skill-eval/skill-forced-eval-hook.sh"

passed=0
failed=0

STATE_DIR="$(mktemp -d)"

# safety: verify the dir is under /tmp or $TMPDIR before allowing any rm operations
assert_temp_dir() {
    local dir="$1"
    local tmpbase="${TMPDIR:-/tmp}"
    tmpbase="${tmpbase%/}"
    case "$dir" in "$tmpbase"/*) ;; *) echo "FATAL: $dir is not under $tmpbase, refusing to proceed" >&2; exit 1;; esac
}
assert_temp_dir "$STATE_DIR"

cleanup() { chmod -R u+w "$STATE_DIR" 2>/dev/null || true; rm -rf "$STATE_DIR"; }
trap cleanup EXIT

run_hook() {
    # $1 = JSON payload; extra args are VAR=value environment overrides
    local payload="$1"
    shift
    printf '%s' "$payload" | env CC_THINGZ_SKILL_EVAL_STATE_DIR="$STATE_DIR" "$@" sh "$HOOK"
}

payload() {
    # $1 = conversationId, $2 = executionId, $3 = invocationNum
    printf '{"conversationId":"%s","executionId":"%s","initialNumSteps":12,"invocationNum":%s,"lastUserInput":"go"}' "$1" "$2" "$3"
}

check() {
    local name="$1" cond="$2"
    if [ "$cond" = "yes" ]; then
        echo "PASS: $name"
        passed=$((passed + 1))
    else
        echo "FAIL: $name"
        failed=$((failed + 1))
    fi
}

injects() {
    # yes when the output is valid JSON with one ephemeralMessage step
    printf '%s' "$1" | python3 -c '
import json, sys
d = json.load(sys.stdin)
steps = d.get("injectSteps", [])
ok = len(steps) == 1 and "MANDATORY SKILL ACTIVATION" in steps[0].get("ephemeralMessage", "")
print("yes" if ok else "no")'
}

is_empty_object() {
    printf '%s' "$1" | python3 -c 'import json, sys; print("yes" if json.load(sys.stdin) == {} else "no")'
}

echo "testing skill-forced-eval-hook.sh"
echo "================================="

out="$(run_hook "$(payload conv-a exec-1 0)")"
check "first model call of a turn injects" "$(injects "$out")"

out="$(run_hook "$(payload conv-a exec-1 1)")"
check "later model call of the same turn prints {}" "$(is_empty_object "$out")"

out="$(run_hook "$(payload conv-a exec-1 7)")"
check "still {} after more tool calls in the same turn" "$(is_empty_object "$out")"

out="$(run_hook "$(payload conv-a exec-2 0)")"
check "a new turn (new executionId) injects again" "$(injects "$out")"

out="$(run_hook "$(payload conv-b exec-1 3)")"
check "another conversation (e.g. a subagent) tracks its own turns" "$(injects "$out")"

out="$(run_hook "$(payload conv-a exec-2 2)")"
check "the first conversation is unaffected by the second" "$(is_empty_object "$out")"

out="$(run_hook '{"conversationId":"conv-c","initialNumSteps":40,"invocationNum":2}')"
check "without executionId, initialNumSteps keys the turn (first call injects)" "$(injects "$out")"
out="$(run_hook '{"conversationId":"conv-c","initialNumSteps":40,"invocationNum":3}')"
check "without executionId, same initialNumSteps prints {}" "$(is_empty_object "$out")"
out="$(run_hook '{"conversationId":"conv-c","initialNumSteps":55,"invocationNum":0}')"
check "without executionId, new initialNumSteps injects" "$(injects "$out")"

out="$(run_hook '{}')"
check "empty payload injects (cannot tell turns apart)" "$(injects "$out")"
out="$(run_hook '{}')"
check "empty payload injects every time" "$(injects "$out")"

out="$(run_hook 'not json at all')"
check "malformed payload injects" "$(injects "$out")"

out="$(run_hook '{"executionId":"exec-9"}')"
check "payload without conversationId injects" "$(injects "$out")"

out="$(run_hook "$(payload 'a/../../x' exec-1 0)")"
check "conversationId with path characters falls back to injecting" "$(injects "$out")"
check "no state file escapes the state dir" "$([ ! -e "$STATE_DIR/../x" ] && echo yes || echo no)"

READONLY_DIR="$STATE_DIR/readonly"
mkdir -p "$READONLY_DIR"
chmod a-w "$READONLY_DIR"
out="$(run_hook "$(payload conv-r exec-1 0)" CC_THINGZ_SKILL_EVAL_STATE_DIR="$READONLY_DIR")"
check "unwritable state dir injects" "$(injects "$out")"
out="$(run_hook "$(payload conv-r exec-1 1)" CC_THINGZ_SKILL_EVAL_STATE_DIR="$READONLY_DIR")"
check "unwritable state dir keeps injecting" "$(injects "$out")"
chmod u+w "$READONLY_DIR"

rc=0
run_hook "$(payload conv-a exec-2 4)" >/dev/null || rc=$?
check "exits 0" "$([ "$rc" -eq 0 ] && echo yes || echo no)"

# summary
echo ""
echo "========================"
echo "results: $passed passed, $failed failed"

if [ "$failed" -gt 0 ]; then
    exit 1
fi
