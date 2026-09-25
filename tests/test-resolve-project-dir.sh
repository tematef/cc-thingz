#!/bin/bash
# automated tests for resolve-project-dir.sh
# the script ships byte-identical in every plugin that needs it; this suite
# pins that the copies match, then runs every case against each copy.
# scaffolds temp git (and hg, when available) trees in the shapes the resolver
# must tell apart — plain repo, monorepo sub-project, nested dirs, no VCS

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
COPIES=(
    "$REPO_ROOT/plugins/planning/scripts/resolve-project-dir.sh"
    "$REPO_ROOT/plugins/workflow/skills/backlog/scripts/resolve-project-dir.sh"
)

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

# physical path: the resolver prints pwd -P, and macOS temp dirs sit behind /var -> /private/var
TMP_ROOT="$(cd "$(mktemp -d)" && pwd -P)"
assert_temp_dir "$TMP_ROOT"

cleanup() {
    rm -rf "$TMP_ROOT"
    return 0
}
trap cleanup EXIT

mk_tmp() {
    mktemp -d "$TMP_ROOT/scratch-XXXXXX"
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

make_git_repo() {
    git -C "$1" init -q
}

echo "testing resolve-project-dir.sh"
echo "=============================="

echo ""
echo "test 0: every plugin copy is byte-identical"
for copy in "${COPIES[@]}"; do
    if cmp -s "${COPIES[0]}" "$copy"; then same="identical"; else same="drifted"; fi
    assert_output "copies/${copy#"$REPO_ROOT"/}" "identical" "$same"
done

for RESOLVE in "${COPIES[@]}"; do
    label="${RESOLVE#"$REPO_ROOT"/plugins/}"
    label="${label%%/*}"

    # run the resolver from a directory
    resolve_in() {
        local dir="$1"
        shift
        (cd "$dir" && bash "$RESOLVE" "$@")
    }

    echo ""
    echo "--- copy: $label ---"

    echo ""
    echo "test 1: plain git repo, run from root -> <root>/<subdir>"
    T="$(mk_tmp)"
    make_git_repo "$T"
    assert_output "$label/plain/root" "$T/docs/plans" "$(resolve_in "$T" docs/plans)"
    assert_output "$label/plain/root-backlog" "$T/docs/backlog" "$(resolve_in "$T" docs/backlog)"

    echo ""
    echo "test 2: plain git repo, run from a deep subdir without markers -> <root>/<subdir>"
    mkdir -p "$T/src/pkg/deep"
    assert_output "$label/plain/deep" "$T/docs/plans" "$(resolve_in "$T/src/pkg/deep" docs/plans)"

    echo ""
    echo "test 3: monorepo sub-project with AGENTS.md wins over the root's existing dirs"
    T="$(mk_tmp)"
    make_git_repo "$T"
    mkdir -p "$T/docs/plans" "$T/docs/backlog" "$T/.agents" "$T/subproj/src/pages"
    touch "$T/subproj/AGENTS.md"
    assert_output "$label/subproject/plans" "$T/subproj/docs/plans" "$(resolve_in "$T/subproj" docs/plans)"
    assert_output "$label/subproject/backlog" "$T/subproj/docs/backlog" "$(resolve_in "$T/subproj" docs/backlog)"

    echo ""
    echo "test 4: nested dir inside the sub-project -> sub-project"
    assert_output "$label/subproject/nested" "$T/subproj/docs/backlog" "$(resolve_in "$T/subproj/src/pages" docs/backlog)"

    echo ""
    echo "test 5: run from the monorepo root -> root"
    assert_output "$label/subproject/from-root" "$T/docs/plans" "$(resolve_in "$T" docs/plans)"

    echo ""
    echo "test 6: sub-project marked only by GEMINI.md -> sub-project"
    T="$(mk_tmp)"
    make_git_repo "$T"
    mkdir -p "$T/svc"
    touch "$T/svc/GEMINI.md"
    assert_output "$label/subproject/gemini-md" "$T/svc/docs/plans" "$(resolve_in "$T/svc" docs/plans)"

    echo ""
    echo "test 7: sub-project marked only by .agents/ -> sub-project"
    T="$(mk_tmp)"
    make_git_repo "$T"
    mkdir -p "$T/svc/.agents"
    assert_output "$label/subproject/agents-dir" "$T/svc/docs/plans" "$(resolve_in "$T/svc" docs/plans)"

    echo ""
    echo "test 8: sub-project marked only by the existing target dir -> sub-project"
    T="$(mk_tmp)"
    make_git_repo "$T"
    mkdir -p "$T/svc/docs/backlog/completed" "$T/svc/lib"
    assert_output "$label/subproject/existing-dir" "$T/svc/docs/backlog" "$(resolve_in "$T/svc/lib" docs/backlog)"
    assert_output "$label/subproject/other-dir-not-a-marker" "$T/docs/plans" "$(resolve_in "$T/svc/lib" docs/plans)"

    echo ""
    echo "test 9: never walks past the VCS root, even when a parent has AGENTS.md"
    T="$(mk_tmp)"
    touch "$T/AGENTS.md"
    mkdir -p "$T/repo/sub"
    make_git_repo "$T/repo"
    assert_output "$label/bounded/vcs-root" "$T/repo/docs/plans" "$(resolve_in "$T/repo/sub" docs/plans)"

    echo ""
    echo "test 10: outside any VCS -> working directory, parents ignored"
    T="$(mk_tmp)"
    touch "$T/AGENTS.md"
    mkdir -p "$T/loose"
    assert_output "$label/no-vcs/cwd" "$T/loose/docs/plans" "$(resolve_in "$T/loose" docs/plans)"

    echo ""
    echo "test 11: absolute override -> printed as-is, trailing slash dropped"
    assert_output "$label/override/absolute" "/srv/plans" "$(resolve_in "$T/loose" docs/plans /srv/plans/)"

    echo ""
    echo "test 12: relative override -> resolved against the project root"
    T="$(mk_tmp)"
    make_git_repo "$T"
    mkdir -p "$T/subproj/src"
    touch "$T/subproj/AGENTS.md"
    assert_output "$label/override/relative" "$T/subproj/planning" "$(resolve_in "$T/subproj/src" docs/plans planning)"

    echo ""
    echo "test 13: unexpanded \${user_config.*} override counts as unset"
    # shellcheck disable=SC2016
    assert_output "$label/override/literal-token" "$T/subproj/docs/plans" "$(resolve_in "$T/subproj" docs/plans '${user_config.plans_dir}')"

    echo ""
    echo "test 14: missing <subdir> -> exit 1 with usage on stderr"
    rc=0
    err="$(cd "$T" && bash "$RESOLVE" 2>&1 >/dev/null)" || rc=$?
    assert_output "$label/usage/exit" "1" "$rc"
    case "$err" in *usage*) has_usage="yes" ;; *) has_usage="no" ;; esac
    assert_output "$label/usage/message" "yes" "$has_usage"

    echo ""
    echo "test 15: resolver never creates the directory"
    [ -e "$T/subproj/docs" ] && created="yes" || created="no"
    assert_output "$label/side-effects/none" "no" "$created"

    if command -v hg >/dev/null 2>&1; then
        echo ""
        echo "test 16: hg repo sub-project -> sub-project, bounded by hg root"
        T="$(mk_tmp)"
        touch "$T/AGENTS.md"
        mkdir -p "$T/repo/subproj/src"
        (cd "$T/repo" && hg init)
        touch "$T/repo/subproj/AGENTS.md"
        assert_output "$label/hg/subproject" "$T/repo/subproj/docs/plans" "$(resolve_in "$T/repo/subproj/src" docs/plans)"
        rm "$T/repo/subproj/AGENTS.md"
        assert_output "$label/hg/bounded" "$T/repo/docs/plans" "$(resolve_in "$T/repo/subproj/src" docs/plans)"
    fi
done

echo ""
echo "======================================"
echo "results: $passed passed, $failed failed"

if [ "$failed" -gt 0 ]; then
    exit 1
fi
