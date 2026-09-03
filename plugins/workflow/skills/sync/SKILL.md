---
name: cc-thingz-sync
description: Syncs the local cc-thingz fork with the upstream umputun/cc-thingz repository, rebases local changes, preserves Antigravity/Jetski adaptations, and runs verification tests.
allowed-tools: run_command, view_file, write_to_file, replace_file_content, ask_question, find_by_name, grep_search
---

# cc-thingz Sync Skill

This skill pulls in updates from the original upstream repository (`https://github.com/umputun/cc-thingz.git`) and reapplies our Google Antigravity (AGY) and Jetski adaptations on top.

## Workflow

When the user requests to sync or update `cc-thingz` from upstream, follow these steps:

### 1. Pre-flight Checks
Verify git status is clean:
```bash
git status --porcelain
```
If there are uncommitted changes, ask the user to stash or commit them first before proceeding.

Ensure the `upstream` remote is configured:
```bash
git remote -v | grep upstream
```
If missing, add it:
```bash
git remote add upstream https://github.com/umputun/cc-thingz.git
```

### 2. Fetch Upstream
Fetch latest changes from upstream:
```bash
git fetch upstream
```

### 3. Rebase
Rebase current branch (typically `master`) onto `upstream/master`:
```bash
git rebase upstream/master
```

If conflicts occur:
- **Do NOT overwrite AGY/Jetski adaptations**:
  - `plugin.json` in each plugin directory must remain.
  - `hooks.json` must remain at the root of `plugins/<name>/hooks.json` (not under `hooks/`).
  - `.agents/` context files (`AGENTS.md`, `CONTEXT.md`) and `install.sh` must be preserved.
  - Hook implementations (`plan-review-hook.py`, `skill-forced-eval-hook.sh`) must maintain AGY `Stop` / `PreInvocation` JSON contracts.
  - Tool calls in `SKILL.md` files must use AGY tools (`invoke_subagent`, `run_command`, `ask_question`, etc.) rather than Claude Code tools (`Agent`, `Bash`, `AskUserQuestion`, etc.).
- If assistance is needed to resolve a conflict, use `ask_question` to confirm the resolution with the user.

### 4. Audit for Claude Code Leaks
After rebase completes, check if new upstream commits introduced any legacy Claude Code tool calls or paths:
```bash
grep -rn '\bBash tool\b\|\bAgent tool\b\|\bAskUserQuestion\b\|\bEnterPlanMode\b\|\bEnterWorktree\b\|\$CLAUDE_PLUGIN_ROOT' plugins/
```
If any matches are found, adapt them to AGY tool names and paths.

### 5. Run Test Suite
Run the test suite to ensure all tests pass:
```bash
for t in tests/test-*.sh; do bash "$t" || echo "FAIL: $t"; done
```

### 6. Verify Installation
Ensure plugins remain registered in `~/.gemini/config/plugins.json`:
```bash
./install.sh
```

### 7. Report Summary
Summarize for the user:
- What upstream commits were integrated.
- Any conflicts resolved or new skills adapted.
- Test suite pass status.
