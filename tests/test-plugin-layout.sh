#!/bin/bash
# cross-plugin guard for the AGY plugin bundle layout
# AGY/Jetski loads skills/, agents/, rules/, hooks.json, mcp_config.json and
# sidecars/ from a plugin, but not commands/. upstream (Claude Code) shipped
# /planning:make as commands/make.md, which therefore never loaded here. this
# suite pins the invariants of the port:
#   - no plugins/*/commands/ directory exists
#   - every plugins/*/skills/*/SKILL.md has a name and a description
#   - every plugins/*/agents/*.md uses AGY markdown-agent frontmatter: name,
#     description, tools as AGY tool names (no Claude Read/Glob/Grep/Bash),
#     no Claude-only fields (color, model: opus/sonnet/haiku)
#   - the ported make-plan skill exists and plan-review is a subagent
#   - /planning:make is only mentioned as a trigger phrase or as upstream history

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "testing plugin bundle layout"
echo "============================"

python3 - "$REPO_ROOT" <<'PY'
import glob
import os
import re
import sys

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


def frontmatter(path):
    """return the frontmatter as {key: raw value} plus list items under a key, or None."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fields, current = {}, None
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            current = m.group(1)
            fields[current] = m.group(2).strip()
        elif current and re.match(r"^\s+-\s+", line):
            fields[current] = (fields[current] + " " + line.strip()[1:].strip()).strip()
    return fields


rel = lambda p: os.path.relpath(p, repo)

# 1. no commands/ directories
commands_dirs = sorted(glob.glob(os.path.join(repo, "plugins", "*", "commands")))
check("no plugins/*/commands/ directory (AGY does not load it)", not commands_dirs,
      ", ".join(rel(d) for d in commands_dirs))

# 2. skills have name + description
skills = sorted(glob.glob(os.path.join(repo, "plugins", "*", "skills", "*", "SKILL.md")))
check("plugins ship at least one skill", bool(skills))
for path in skills:
    fm = frontmatter(path) or {}
    check(f"{rel(path)}: name and description", bool(fm.get("name")) and bool(fm.get("description")), repr(fm)[:200])

# 3. agents use AGY frontmatter
claude_tools = {"Read", "Write", "Edit", "Glob", "Grep", "Bash", "Agent", "Task", "AskUserQuestion"}
agents = sorted(glob.glob(os.path.join(repo, "plugins", "*", "agents", "*.md")))
for path in agents:
    fm = frontmatter(path)
    label = rel(path)
    check(f"{label}: has frontmatter", fm is not None)
    if fm is None:
        continue
    check(f"{label}: name and description", bool(fm.get("name")) and bool(fm.get("description")))
    tools = set(re.split(r"[\s,\[\]]+", fm.get("tools", ""))) - {""}
    check(f"{label}: no Claude Code tool names in tools", not (tools & claude_tools), str(sorted(tools & claude_tools)))
    check(f"{label}: no Claude-only color field", "color" not in fm)
    check(f"{label}: model is an AGY tier", fm.get("model", "inherit") in {"inherit", "flash_lite", "flash", "pro"},
          fm.get("model", ""))

# 4. the port itself
make_plan = os.path.join(repo, "plugins", "planning", "skills", "make-plan", "SKILL.md")
check("planning ships the make-plan skill", os.path.isfile(make_plan))
if os.path.isfile(make_plan):
    check("make-plan: name is make-plan", (frontmatter(make_plan) or {}).get("name") == "make-plan")
plan_review = os.path.join(repo, "plugins", "planning", "agents", "plan-review.md")
check("plan-review agent is invokable as a subagent",
      os.path.isfile(plan_review) and (frontmatter(plan_review) or {}).get("subagent") == "true")

# 5. /planning:make survives only as a trigger phrase or upstream history
allowed = {
    os.path.join("plugins", "planning", "skills", "make-plan", "SKILL.md"),  # trigger phrase in description
    os.path.join("plugins", "planning", "references", "usage.md"),            # port note + trigger list
    "README.md",                                                               # "what differs from upstream"
    os.path.join(".agents", "AGENTS.md"),                                     # porting rule
}
offenders = []
for root in ("plugins", ".agents", "README.md"):
    base = os.path.join(repo, root)
    files = [base] if os.path.isfile(base) else [
        os.path.join(d, f) for d, _, fs in os.walk(base) if "__pycache__" not in d for f in fs
    ]
    for path in files:
        if rel(path) in allowed or not path.endswith((".md", ".sh", ".py", ".json", ".txt")):
            continue
        with open(path, encoding="utf-8", errors="ignore") as f:
            if "/planning:make" in f.read():
                offenders.append(rel(path))
check("no stale /planning:make references", not offenders, ", ".join(sorted(offenders)))

print("\n======================================")
print(f"results: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
PY
