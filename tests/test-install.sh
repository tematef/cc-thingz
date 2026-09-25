#!/bin/bash
# integration tests for install.sh
# runs the default (no-argument) install against a throwaway HOME and asserts on
# plugins.json, the plugin links and the global hooks.json. The default run never
# mutates the repository; --exclude/--restore move skill dirs and are not exercised.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
INSTALL="$REPO_ROOT/install.sh"
PLUGIN_DIR="$REPO_ROOT/plugins"

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

check() {
    local desc="$1"
    shift
    if "$@"; then
        echo "PASS: $desc"
        passed=$((passed + 1))
    else
        echo "FAIL: $desc"
        failed=$((failed + 1))
    fi
}

# fresh fake HOME with the given global hooks.json content (empty = no file)
mk_home() {
    local home hooks="${1:-}"
    home="$(mktemp -d "$TMP_ROOT/home-XXXXXX")"
    mkdir -p "$home/.gemini/config/plugins"
    if [ -n "$hooks" ]; then
        printf '%s\n' "$hooks" > "$home/.gemini/config/hooks.json"
    fi
    echo "$home"
}

run_install() {
    HOME="$1" bash "$INSTALL" > "$1/install.out" 2>&1
}

hooks_keys() {
    python3 -c 'import json,sys; print(" ".join(sorted(json.load(open(sys.argv[1])))))' "$1"
}

STALE_GUARD='"autonomous-exec-guard": {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "python3 \"/some/checkout/plugins/planning/scripts/autonomous-exec-hook.py\"", "timeout": 10}]}]}'
OTHER_HOOK='"generic-task-cleanup": {"Stop": [{"type": "command", "command": "echo {}"}]}'

echo "=== fresh install ==="
home="$(mk_home)"
check "install exits 0" run_install "$home"
cfg="$home/.gemini/config"
check "plugins.json registers the repo plugins dir" \
    python3 -c 'import json,sys; e=json.load(open(sys.argv[1]))["entries"]; sys.exit(0 if {"path": sys.argv[2]} in e else 1)' \
    "$cfg/plugins.json" "$PLUGIN_DIR"
all_linked=0
for p in "$PLUGIN_DIR"/*/; do
    name="$(basename "$p")"
    if [ "$(readlink "$cfg/plugins/$name")" != "$PLUGIN_DIR/$name" ]; then
        all_linked=1
        echo "  missing or wrong link: $name"
    fi
done
check "every plugin is linked into config/plugins" test "$all_linked" -eq 0
check "no global hooks.json is created" test ! -e "$cfg/hooks.json"

echo "=== dangling links ==="
home="$(mk_home)"
cfg="$home/.gemini/config"
ln -s "$PLUGIN_DIR/removed-plugin-xyz" "$cfg/plugins/removed-plugin-xyz"
ln -s "$TMP_ROOT/elsewhere/foreign" "$cfg/plugins/foreign-dangling"
run_install "$home"
check "dangling link into this repo is pruned" test ! -L "$cfg/plugins/removed-plugin-xyz"
check "prune is reported" grep -q "Removed dangling plugin link" "$home/install.out"
check "foreign dangling link is left alone" test -L "$cfg/plugins/foreign-dangling"

echo "=== stale global autonomous-exec-guard ==="
home="$(mk_home "{$STALE_GUARD, $OTHER_HOOK}")"
cfg="$home/.gemini/config"
run_install "$home"
check "stale global guard is removed, other hooks kept" \
    test "$(hooks_keys "$cfg/hooks.json")" = "generic-task-cleanup"
check "removal is reported" grep -q "Removed duplicate autonomous-exec-guard" "$home/install.out"
before="$(cat "$cfg/hooks.json")"
run_install "$home"
check "second run leaves hooks.json unchanged" test "$(cat "$cfg/hooks.json")" = "$before"

echo "=== foreign hook under the same name ==="
home="$(mk_home '{"autonomous-exec-guard": {"PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "my-own-guard.sh"}]}]}}')"
cfg="$home/.gemini/config"
run_install "$home"
check "a guard that does not run autonomous-exec-hook.py is kept" \
    test "$(hooks_keys "$cfg/hooks.json")" = "autonomous-exec-guard"

echo "=== unparseable hooks.json ==="
home="$(mk_home '{ not json')"
cfg="$home/.gemini/config"
check "install still exits 0" run_install "$home"
check "unparseable hooks.json is left byte-identical" test "$(cat "$cfg/hooks.json")" = "{ not json"
check "a warning is printed" grep -q "could not be parsed" "$home/install.out"

echo "=== no global guard is ever added ==="
home="$(mk_home "{$OTHER_HOOK}")"
cfg="$home/.gemini/config"
run_install "$home"
check "existing global hooks are untouched" \
    test "$(hooks_keys "$cfg/hooks.json")" = "generic-task-cleanup"

echo ""
echo "======================================"
echo "results: $passed passed, $failed failed"

if [ "$failed" -gt 0 ]; then
    exit 1
fi
