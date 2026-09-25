#!/bin/bash
# integration tests for plugins/planning/scripts/ralphex-plans-link-hook.py
# builds throwaway git repos in the shapes the hook must tell apart, feeds a
# real PreInvocation payload on stdin and asserts on stdout and the filesystem

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
HOOK="$REPO_ROOT/plugins/planning/scripts/ralphex-plans-link-hook.py"

passed=0
failed=0

assert_temp_dir() {
    local dir="$1"
    local tmpbase="${TMPDIR:-/tmp}"
    tmpbase="${tmpbase%/}"
    case "$dir" in
    "$tmpbase"/*) ;;
    /tmp/*) ;;
    /private/tmp/*) ;;
    /private/var/*) ;;
    /var/folders/*) ;;
    *)
        echo "FATAL: $dir is not under a recognised temp base, refusing to proceed" >&2
        exit 1
        ;;
    esac
}

TMP_ROOT="$(cd "$(mktemp -d)" && pwd -P)"
assert_temp_dir "$TMP_ROOT"

cleanup() {
    rm -rf "$TMP_ROOT"
    return 0
}
trap cleanup EXIT

mk_repo() {
    local dir
    dir="$(mktemp -d "$TMP_ROOT/repo-XXXXXX")"
    git -C "$dir" init -q
    git -C "$dir" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
    echo "$dir"
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

# run the hook for one or more workspace paths; prints stdout only
run_hook() {
    local paths="" p
    for p in "$@"; do
        paths="$paths${paths:+,}\"$p\""
    done
    printf '{"conversationId":"test","invocationNum":1,"workspacePaths":[%s]}' "$paths" |
        python3 "$HOOK" 2>/dev/null
}

kind() {
    if [ -L "$1" ]; then
        echo "symlink:$(readlink "$1")"
    elif [ -d "$1" ]; then
        echo "dir"
    elif [ -e "$1" ]; then
        echo "file"
    else
        echo "missing"
    fi
}

echo "testing ralphex-plans-link-hook.py"
echo "=================================="

echo ""
echo "test 1: no .ralphex anywhere -> nothing created"
R="$(mk_repo)"
assert_output "no-ralphex/stdout" "{}" "$(run_hook "$R")"
assert_output "no-ralphex/.ralphex" "missing" "$(kind "$R/.ralphex")"
assert_output "no-ralphex/docs" "missing" "$(kind "$R/docs")"

echo ""
echo "test 2: .ralphex at the project root -> relative link to ../docs/plans"
R="$(mk_repo)"
mkdir "$R/.ralphex"
assert_output "root/stdout" "{}" "$(run_hook "$R")"
assert_output "root/link" "symlink:../docs/plans" "$(kind "$R/.ralphex/plans")"
assert_output "root/docs-plans" "dir" "$(kind "$R/docs/plans")"

echo ""
echo "test 3: .ralphex only at repo root, sub-project with AGENTS.md -> link into sub-project"
R="$(mk_repo)"
mkdir -p "$R/.ralphex" "$R/sub/src"
touch "$R/AGENTS.md" "$R/sub/AGENTS.md"
assert_output "subproject/stdout" "{}" "$(run_hook "$R/sub")"
assert_output "subproject/link" "symlink:../sub/docs/plans" "$(kind "$R/.ralphex/plans")"
assert_output "subproject/docs-plans" "dir" "$(kind "$R/sub/docs/plans")"
assert_output "subproject/no-root-docs" "missing" "$(kind "$R/docs")"

echo ""
echo "test 4: second run is a no-op"
before="$(ls -li "$R/.ralphex" | grep plans)"
assert_output "idempotent/stdout" "{}" "$(run_hook "$R/sub")"
assert_output "idempotent/same-entry" "$before" "$(ls -li "$R/.ralphex" | grep plans)"

echo ""
echo "test 4a: a root session after the sub-project keeps the shared link on the sub-project"
assert_output "shared-first-wins/stdout" "{}" "$(run_hook "$R")"
assert_output "shared-first-wins/link" "symlink:../sub/docs/plans" "$(kind "$R/.ralphex/plans")"
assert_output "shared-first-wins/no-root-docs" "missing" "$(kind "$R/docs")"
assert_output "shared-first-wins/same-entry" "$before" "$(ls -li "$R/.ralphex" | grep plans)"

echo ""
echo "test 5: existing link pointing elsewhere is never re-pointed"
R="$(mk_repo)"
mkdir -p "$R/.ralphex" "$R/elsewhere"
ln -s ../elsewhere "$R/.ralphex/plans"
assert_output "foreign-link/stdout" "{}" "$(run_hook "$R")"
assert_output "foreign-link/unchanged" "symlink:../elsewhere" "$(kind "$R/.ralphex/plans")"
assert_output "foreign-link/no-docs" "missing" "$(kind "$R/docs")"

echo ""
echo "test 6: empty real .ralphex/plans is replaced with the link"
R="$(mk_repo)"
mkdir -p "$R/.ralphex/plans"
assert_output "empty-dir/stdout" "{}" "$(run_hook "$R")"
assert_output "empty-dir/link" "symlink:../docs/plans" "$(kind "$R/.ralphex/plans")"

echo ""
echo "test 7: .ralphex/plans holding plans (untracked and tracked) is left untouched"
R="$(mk_repo)"
mkdir -p "$R/.ralphex/plans/completed"
echo "old" >"$R/.ralphex/plans/old.md"
echo "done" >"$R/.ralphex/plans/completed/done.md"
sum_before="$(cd "$R" && find .ralphex -type f -exec cksum {} + | sort)"
assert_output "untracked/stdout" "{}" "$(run_hook "$R")"
assert_output "untracked/dir" "dir" "$(kind "$R/.ralphex/plans")"
assert_output "untracked/bytes" "$sum_before" "$(cd "$R" && find .ralphex -type f -exec cksum {} + | sort)"
assert_output "untracked/no-docs" "missing" "$(kind "$R/docs")"
git -C "$R" add -f .ralphex/plans
git -C "$R" -c user.email=t@t -c user.name=t commit -q -m plans
assert_output "tracked/stdout" "{}" "$(run_hook "$R")"
assert_output "tracked/dir" "dir" "$(kind "$R/.ralphex/plans")"
assert_output "tracked/clean" "" "$(git -C "$R" status --porcelain)"

echo ""
echo "test 8: two workspaces, only the one using ralphex is linked"
A="$(mk_repo)"
B="$(mk_repo)"
mkdir "$B/.ralphex"
assert_output "multi/stdout" "{}" "$(run_hook "$A" "$B")"
assert_output "multi/a-untouched" "missing" "$(kind "$A/.ralphex")"
assert_output "multi/b-linked" "symlink:../docs/plans" "$(kind "$B/.ralphex/plans")"

echo ""
echo "test 9: bad input and non-VCS workspaces never fail"
N="$(mktemp -d "$TMP_ROOT/novcs-XXXXXX")"
mkdir "$N/.ralphex"
assert_output "bad/empty-stdin" "{}" "$(printf '' | python3 "$HOOK" 2>/dev/null)"
assert_output "bad/garbage" "{}" "$(printf 'not json' | python3 "$HOOK" 2>/dev/null)"
assert_output "bad/wrong-type" "{}" "$(printf '{"workspacePaths":"x"}' | python3 "$HOOK" 2>/dev/null)"
assert_output "bad/missing-path" "{}" "$(run_hook "$TMP_ROOT/does-not-exist")"
assert_output "bad/no-vcs-stdout" "{}" "$(run_hook "$N")"
assert_output "bad/no-vcs-untouched" "missing" "$(kind "$N/.ralphex/plans")"
set +e
printf 'not json' | python3 "$HOOK" >/dev/null 2>&1
rc=$?
set -e
assert_output "bad/exit-0" "0" "$rc"

echo ""
echo "test 10: a plan written and archived through the link lands in docs/plans/completed"
R="$(mk_repo)"
mkdir "$R/.ralphex"
run_hook "$R" >/dev/null
echo "plan" >"$R/.ralphex/plans/x.md"
mkdir -p "$R/.ralphex/plans/completed"
mv "$R/.ralphex/plans/x.md" "$R/.ralphex/plans/completed/x.md"
assert_output "flow/archived" "plan" "$(cat "$R/docs/plans/completed/x.md")"
assert_output "flow/source-gone" "missing" "$(kind "$R/docs/plans/x.md")"

echo ""
echo "test 11: relative link survives moving the repository"
MOVED="$TMP_ROOT/moved-repo"
mv "$R" "$MOVED"
assert_output "moved/resolves" "plan" "$(cat "$MOVED/.ralphex/plans/completed/x.md")"

echo ""
echo "test 12: git refuses paths through the link, accepts the real path (ralphex commit note)"
set +e
git -C "$MOVED" add .ralphex/plans/completed/x.md >/dev/null 2>&1
rc_link=$?
git -C "$MOVED" add docs/plans/completed/x.md >/dev/null 2>&1
rc_real=$?
set -e
assert_output "git/through-link-refused" "128" "$rc_link"
assert_output "git/real-path-ok" "0" "$rc_real"

echo ""
echo "======================================"
echo "results: $passed passed, $failed failed"

if [ "$failed" -gt 0 ]; then
    exit 1
fi
