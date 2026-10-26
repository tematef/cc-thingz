#!/bin/bash
# guard for the headless fallback in interactive skills
# under `agy -p` / Jetski print mode and in subagents the ask_question tool is
# unavailable; a live spike showed agents then ask in plain text and stop
# without a deliverable. every skill that uses ask_question must therefore
# carry the same "When no one can answer" section, byte-identical across
# skills, placed before the skill's first other "## " heading.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "testing headless fallback in interactive skills"

python3 - "$REPO_ROOT" <<'PY'
import glob
import os
import re
import sys

root = sys.argv[1]
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}" + (f" ({detail})" if detail else ""))


HEADING = "## When no one can answer"
skills = sorted(glob.glob(os.path.join(root, "plugins/*/skills/*/SKILL.md")))
interactive = []
for path in skills:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if "ask_question" in text:
        interactive.append((os.path.relpath(path, root), text))

check("at least one interactive skill found", bool(interactive))

sections = {}
for rel, text in interactive:
    m = re.search(r"^## When no one can answer\n(.*?)(?=^## )", text, re.M | re.S)
    check(f"{rel}: has '{HEADING}' section", m is not None)
    if not m:
        continue
    sections[rel] = m.group(1)
    first_h2 = re.search(r"^## .*$", text, re.M).group(0)
    check(f"{rel}: section is the first '## ' heading", first_h2 == HEADING, first_h2)
    body = m.group(1)
    for needle in ("ask_question", "headless", "subagent", "recommended", "safer option"):
        check(f"{rel}: section mentions '{needle}'", needle in body)

check(
    "section text is identical in every interactive skill",
    len(set(sections.values())) <= 1,
    ", ".join(sorted(sections)),
)

exec_path = os.path.join(root, "plugins/planning/skills/exec/SKILL.md")
with open(exec_path, encoding="utf-8") as f:
    exec_text = f.read()
check(
    "exec worktree question names its headless default",
    '"When no one can answer" case above' in exec_text and '"Stay here" (Case B)' in exec_text,
)

print("\n======================================")
print(f"results: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
PY
