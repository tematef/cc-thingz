#!/bin/bash
# automated tests for resolve-rules.sh
# exercises the two-layer resolution chain (.agents/ project override, then
# user data dir) with various scenarios, and pins that the Claude Code
# .claude/ override and $CLAUDE_PLUGIN_DATA are no longer consulted

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
RESOLVE_SCRIPT="$REPO_ROOT/plugins/planning/scripts/resolve-rules.sh"
TEST_FILENAME="test-rules.md"

passed=0
failed=0

# setup temp working directory to avoid polluting the real working directory
WORK_DIR="$(mktemp -d)"
USER_DIR="$(mktemp -d)"

# safety: verify dirs are under /tmp or $TMPDIR before allowing any rm operations
assert_temp_dir() {
    local dir="$1"
    local tmpbase="${TMPDIR:-/tmp}"
    tmpbase="${tmpbase%/}"
    case "$dir" in "$tmpbase"/*) ;; *) echo "FATAL: $dir is not under $tmpbase, refusing to proceed" >&2; exit 1;; esac
}
assert_temp_dir "$WORK_DIR"
assert_temp_dir "$USER_DIR"

cleanup() { rm -rf "$WORK_DIR" "$USER_DIR"; }
trap cleanup EXIT

run_resolve() {
    # run from the temp work directory with data dir passed as argument (primary mechanism)
    (cd "$WORK_DIR" && bash "$RESOLVE_SCRIPT" "$TEST_FILENAME" "$USER_DIR")
}

run_resolve_env() {
    # run from the temp work directory with GEMINI_PLUGIN_DATA as env var (fallback)
    (cd "$WORK_DIR" && GEMINI_PLUGIN_DATA="$USER_DIR" bash "$RESOLVE_SCRIPT" "$TEST_FILENAME")
}

assert_output() {
    local test_name="$1"
    local expected="$2"
    local actual="$3"
    if [ "$expected" = "$actual" ]; then
        echo "  PASS: $test_name"
        passed=$((passed + 1))
    else
        echo "  FAIL: $test_name"
        echo "    expected: $(printf '%q' "$expected")"
        echo "    actual:   $(printf '%q' "$actual")"
        failed=$((failed + 1))
    fi
}

assert_empty() {
    local test_name="$1"
    local actual="$2"
    if [ -z "$actual" ]; then
        echo "  PASS: $test_name"
        passed=$((passed + 1))
    else
        echo "  FAIL: $test_name"
        echo "    expected empty output"
        echo "    actual: $(printf '%q' "$actual")"
        failed=$((failed + 1))
    fi
}

echo "testing resolve-rules.sh"
echo "========================"

# test 1: no files present - empty output
echo ""
echo "test 1: no files present"
rm -rf "$WORK_DIR/.agents" "$WORK_DIR/.claude"
rm -f "${USER_DIR:?}/$TEST_FILENAME"
output="$(run_resolve)"
assert_empty "no files produces empty output" "$output"

# test 2: only .agents file - outputs .agents content
echo ""
echo "test 2: only .agents file"
mkdir -p "$WORK_DIR/.agents"
echo "agents rules content" > "$WORK_DIR/.agents/$TEST_FILENAME"
rm -f "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve)"
assert_output ".agents file content returned" "agents rules content" "$output"

rm -rf "$WORK_DIR/.agents"

# test 3: only user file - outputs user content
echo ""
echo "test 3: only user file"
echo "user rules content" > "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve)"
assert_output "user file content returned" "user rules content" "$output"

rm -f "$USER_DIR/$TEST_FILENAME"

# test 4: .agents and user present - .agents wins (first-found-wins)
echo ""
echo "test 4: .agents and user present (.agents wins)"
mkdir -p "$WORK_DIR/.agents"
echo "agents rules content" > "$WORK_DIR/.agents/$TEST_FILENAME"
echo "user rules content" > "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve)"
assert_output ".agents takes precedence over user" "agents rules content" "$output"

rm -rf "$WORK_DIR/.agents"
rm -f "$USER_DIR/$TEST_FILENAME"

# test 5: empty .agents file - empty output
echo ""
echo "test 5: empty .agents file"
mkdir -p "$WORK_DIR/.agents"
touch "$WORK_DIR/.agents/$TEST_FILENAME"
output="$(run_resolve)"
assert_empty "empty file produces empty output" "$output"

# test 5b: empty .agents file, non-empty user file - user wins
echo ""
echo "test 5b: empty .agents file with user file present"
echo "user rules content" > "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve)"
assert_output "user file returned when .agents file is empty" "user rules content" "$output"

rm -rf "$WORK_DIR/.agents"
rm -f "$USER_DIR/$TEST_FILENAME"

# test 6: legacy .claude/ project override is ignored
echo ""
echo "test 6: .claude/ override is ignored"
mkdir -p "$WORK_DIR/.claude"
echo "claude rules content" > "$WORK_DIR/.claude/$TEST_FILENAME"
output="$(run_resolve)"
assert_empty ".claude file alone produces empty output" "$output"
echo "user rules content" > "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve)"
assert_output "user file wins over .claude file" "user rules content" "$output"

rm -rf "$WORK_DIR/.claude"
rm -f "$USER_DIR/$TEST_FILENAME"

# test 7: no filename argument - empty output
echo ""
echo "test 7: no filename argument"
output="$( (cd "$WORK_DIR" && bash "$RESOLVE_SCRIPT") )"
assert_empty "no argument produces empty output" "$output"

# test 8: no data dir and no env var - only project path checked
echo ""
echo "test 8: no data dir argument and no env var"
mkdir -p "$WORK_DIR/.agents"
echo "project only" > "$WORK_DIR/.agents/$TEST_FILENAME"
output="$( (cd "$WORK_DIR" && unset GEMINI_PLUGIN_DATA && bash "$RESOLVE_SCRIPT" "$TEST_FILENAME") )"
assert_output "works without data dir or env var" "project only" "$output"

rm -rf "$WORK_DIR/.agents"

# test 9: env var fallback when no argument provided
echo ""
echo "test 9: GEMINI_PLUGIN_DATA fallback (no data-dir argument)"
echo "user via env" > "$USER_DIR/$TEST_FILENAME"
output="$(run_resolve_env)"
assert_output "env var fallback works" "user via env" "$output"

# test 9b: legacy CLAUDE_PLUGIN_DATA is ignored
echo ""
echo "test 9b: CLAUDE_PLUGIN_DATA is ignored"
output="$( (cd "$WORK_DIR" && unset GEMINI_PLUGIN_DATA && CLAUDE_PLUGIN_DATA="$USER_DIR" bash "$RESOLVE_SCRIPT" "$TEST_FILENAME") )"
assert_empty "CLAUDE_PLUGIN_DATA not consulted" "$output"

rm -f "$USER_DIR/$TEST_FILENAME"

# test 10: argument takes precedence over env var
echo ""
echo "test 10: argument overrides env var"
ALT_DIR="$(mktemp -d)"
assert_temp_dir "$ALT_DIR"
echo "from argument" > "$ALT_DIR/$TEST_FILENAME"
echo "from env var" > "$USER_DIR/$TEST_FILENAME"
output="$( (cd "$WORK_DIR" && GEMINI_PLUGIN_DATA="$USER_DIR" bash "$RESOLVE_SCRIPT" "$TEST_FILENAME" "$ALT_DIR") )"
assert_output "argument overrides env var" "from argument" "$output"

rm -rf "$ALT_DIR" "${USER_DIR:?}/$TEST_FILENAME"

# summary
echo ""
echo "========================"
echo "results: $passed passed, $failed failed"

if [ "$failed" -gt 0 ]; then
    exit 1
fi
