#!/bin/bash
# cross-plugin guard for plugins/*/hooks.json
# AGY/Jetski merges hooks from every plugin and runs the handlers of one event
# in sequence; hooks are keyed by name, so a repeated name across plugins can
# shadow another plugin's hook. this suite pins the invariants that keep the
# hooks from interfering with each other:
#   - every hooks.json parses and sits at its plugin root (never under hooks/)
#   - hook names are unique across all plugins
#   - tool events (PreToolUse/PostToolUse) use the grouped matcher form,
#     the other events use the flat handler list
#   - every script a handler references exists relative to its plugin root
#   - each PreInvocation/PreToolUse handler, fed a minimal payload, prints
#     JSON of the shape its event expects and exits 0. Stop handlers are only
#     checked structurally: plan-review-hook may legitimately block for hours.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "testing plugins/*/hooks.json"
echo "============================"

python3 - "$REPO_ROOT" <<'PY'
import glob
import json
import os
import shlex
import subprocess
import sys
import tempfile

repo = sys.argv[1]
passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}" + (f"\n    {detail}" if detail else ""))


TOOL_EVENTS = {"PreToolUse", "PostToolUse"}
FLAT_EVENTS = {"PreInvocation", "PostInvocation", "Stop"}
KNOWN_KEYS = TOOL_EVENTS | FLAT_EVENTS | {"enabled"}

print("\ntest 1: placement")
nested = glob.glob(os.path.join(repo, "plugins", "*", "hooks", "hooks.json"))
check("no hooks.json nested under hooks/", not nested, str(nested))
files = sorted(glob.glob(os.path.join(repo, "plugins", "*", "hooks.json")))
check("at least one plugin hooks.json", bool(files))

print("\ntest 2: parse, names, structure, referenced scripts")
owners = {}
handlers = []  # (plugin_dir, hook_name, event, handler)
for path in files:
    plugin_dir = os.path.dirname(path)
    plugin = os.path.basename(plugin_dir)
    try:
        with open(path) as fh:
            data = json.load(fh)
        ok = isinstance(data, dict)
    except ValueError as exc:
        data, ok = {}, False
    check(f"{plugin}: valid JSON object", ok)
    for name, spec in data.items():
        owners.setdefault(name, []).append(plugin)
        check(f"{plugin}/{name}: spec is an object", isinstance(spec, dict))
        if not isinstance(spec, dict):
            continue
        unknown = set(spec) - KNOWN_KEYS
        check(f"{plugin}/{name}: only known events", not unknown, f"unknown: {sorted(unknown)}")
        for event, entries in spec.items():
            if event == "enabled":
                continue
            check(f"{plugin}/{name}/{event}: list", isinstance(entries, list))
            for entry in entries if isinstance(entries, list) else []:
                if event in TOOL_EVENTS:
                    grouped = isinstance(entry, dict) and "matcher" in entry and isinstance(entry.get("hooks"), list)
                    check(f"{plugin}/{name}/{event}: grouped matcher form", grouped)
                    inner = entry.get("hooks", []) if grouped else []
                else:
                    flat = isinstance(entry, dict) and "command" in entry and "hooks" not in entry
                    check(f"{plugin}/{name}/{event}: flat handler form", flat)
                    inner = [entry] if flat else []
                for handler in inner:
                    handlers.append((plugin_dir, name, event, handler))
                    cmd = handler.get("command", "")
                    for token in shlex.split(cmd):
                        if token.endswith((".py", ".sh")):
                            target = os.path.join(plugin_dir, os.path.expanduser(token))
                            check(f"{plugin}/{name}: {token} exists", os.path.isfile(target))

print("\ntest 3: hook names are unique across plugins")
for name, plugins in sorted(owners.items()):
    check(f"'{name}' defined once", len(plugins) == 1, f"defined in: {plugins}")

print("\ntest 4: handler contract smoke tests")
empty_ws = tempfile.mkdtemp()
common = {"conversationId": "hooks-json-test", "workspacePaths": [empty_ws],
          "transcriptPath": "", "artifactDirectoryPath": empty_ws, "modelName": "test"}
for plugin_dir, name, event, handler in handlers:
    label = f"{os.path.basename(plugin_dir)}/{name}/{event}"
    if event == "PreInvocation":
        payload = dict(common, invocationNum=1, initialNumSteps=0)
    elif event == "PreToolUse":
        payload = dict(common, stepIdx=1, toolCall={"name": "view_file", "args": {"AbsolutePath": "/tmp/x"}})
    else:
        print(f"  SKIP: {label} (structure only)")
        continue
    try:
        out = subprocess.run(handler["command"], shell=True, cwd=plugin_dir, input=json.dumps(payload),
                             capture_output=True, text=True, timeout=handler.get("timeout", 30))
        rc, stdout = out.returncode, out.stdout
    except subprocess.TimeoutExpired:
        rc, stdout = "timeout", ""
    check(f"{label}: exit 0", rc == 0, f"rc={rc}")
    try:
        result = json.loads(stdout)
    except ValueError:
        result = None
    check(f"{label}: stdout is a JSON object", isinstance(result, dict), repr(stdout[:200]))
    if not isinstance(result, dict):
        continue
    if event == "PreInvocation":
        steps = result.get("injectSteps", [])
        check(f"{label}: injectSteps is a list", isinstance(steps, list))
    else:
        check(f"{label}: decision present", result.get("decision") in {"allow", "deny", "ask", "force_ask"},
              repr(result))

os.rmdir(empty_ws)
print("\n======================================")
print(f"results: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
PY
