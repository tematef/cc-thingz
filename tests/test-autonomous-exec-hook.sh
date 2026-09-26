#!/usr/bin/env bash
# Test suite for plugins/planning/scripts/autonomous-exec-hook.py

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SCRIPT="$REPO_ROOT/plugins/planning/scripts/autonomous-exec-hook.py"
REPLAY_SCRIPT="$REPO_ROOT/tests/test-autonomous-exec-replay.py"
HOOKS_JSON="$REPO_ROOT/plugins/planning/hooks.json"

export CC_THINGZ_AUTONOMOUS_MARKER="/tmp/cc-thingz-test-nonexistent-marker"

echo "Running embedded unit tests for autonomous-exec-hook.py (using /usr/bin/python3)..."
/usr/bin/python3 "$HOOK_SCRIPT" --test

echo "Running historical subagent & main-agent transcript replay tests..."
/usr/bin/python3 "$REPLAY_SCRIPT"

echo "Verifying stdin JSON pipeline behavior..."
allow_out=$(echo '{"toolCall":{"name":"run_command","args":{"CommandLine":"ls -la | head -5"}}}' | /usr/bin/python3 "$HOOK_SCRIPT")
echo "$allow_out" | grep -q '"decision": "allow"'

orch_out=$(echo '{"toolCall":{"name":"send_message","args":{"Recipient":"sub-1","Message":"done"}}}' | /usr/bin/python3 "$HOOK_SCRIPT")
echo "$orch_out" | grep -q '"decision": "allow"'

reject_out=$(echo '{"toolCall":{"name":"run_command","args":{"CommandLine":"rm -rf src; cat /tmp/x"}}}' | /usr/bin/python3 "$HOOK_SCRIPT")
echo "$reject_out" | grep -q '"decision": "ask"'

block_out=$(echo '{"toolCall":{"name":"run_command","args":{"CommandLine":"rm -fr /"}}}' | /usr/bin/python3 "$HOOK_SCRIPT")
echo "$block_out" | grep -q '"decision": "force_ask"'

echo "Verifying hooks.json registration..."
grep -q '"PreToolUse"' "$HOOKS_JSON"
grep -q 'autonomous-exec-hook.py' "$HOOKS_JSON"

echo "PASS: test-autonomous-exec-hook.sh"
