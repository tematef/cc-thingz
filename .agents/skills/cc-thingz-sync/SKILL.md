---
name: cc-thingz-sync
description: Syncs the local cc-thingz fork with the upstream umputun/cc-thingz repository, rebases local changes, preserves Antigravity/Jetski adaptations, and runs verification tests.
allowed-tools: run_command, view_file, write_to_file, replace_file_content, ask_question, find_by_name, grep_search
---

# cc-thingz Sync Skill

This skill pulls in updates from the original upstream repository (`https://github.com/umputun/cc-thingz.git`) and reapplies our Google Antigravity (AGY) and Jetski adaptations on top.

## Workflow

When the user requests to sync or update `cc-thingz` from upstream (note: when asked to check or use "latest", default to checking `origin` at `tematef/cc-thingz`; only fetch/rebase `upstream` upon explicit user confirmation), follow these steps:

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
git rebase --rebase-merges upstream/master
```

> [!IMPORTANT]
> **Live-hook safety**: Plugins in `~/.gemini/config/plugins/` link directly to this repository. During a rebase, checking out older historical commits where hook scripts (e.g. `autonomous-exec-hook.py`) did not exist will fail AGY's live `PreToolUse` hook and block tool execution. Before rebasing, safeguard active hooks (e.g. copy `plugins/planning` to `/tmp/planning-live-backup` and link `~/.gemini/config/plugins/planning` to it), and run `./install.sh` immediately after the rebase finishes.

If conflicts occur:
- **Do NOT overwrite AGY/Jetski adaptations**:
  - `plugin.json` in each plugin directory must remain.
  - `hooks.json` must remain at the root of `plugins/<name>/hooks.json` (not under `hooks/`).
  - `.agents/AGENTS.md` (the only rules file), `.agents/skills/` and `install.sh` must be preserved. Never let upstream reintroduce a root `AGENTS.md` or `GEMINI.md`, `.agents/CONTEXT.md` or the `.agent` symlink.
  - `.revmux/profile.md` is this fork's review profile; upstream's file at the same path describes upstream's project. During a rebase conflict on `.revmux/profile.md`, keep the fork's copy (`--theirs` during rebase is the commit being replayed) and stage it without committing:
    ```bash
    git checkout --theirs -- .revmux/profile.md && git add .revmux/profile.md
    ```
    After the rebase finishes, verify `.revmux/profile.md` still starts with `# Project profile: cc-thingz (AGY/Jetski fork)`; if an upstream commit overwrote it cleanly without a conflict, restore it from `ORIG_HEAD`:
    ```bash
    git checkout ORIG_HEAD -- .revmux/profile.md && git commit -m "chore: keep the fork's revmux profile"
    ```
  - Hook implementations (`autonomous-exec-hook.py`, `plan-review-hook.py`, `ralphex-plans-link-hook.py`, `skill-forced-eval-hook.sh`) must maintain AGY `PreToolUse` / `Stop` / `PreInvocation` JSON contracts.
  - Tool calls in `SKILL.md` files must use AGY tools (`invoke_subagent`, `run_command`, `ask_question`, etc.) rather than Claude Code tools (`Agent`, `Bash`, `AskUserQuestion`, etc.).
- **Always discard excluded upstream plugins, skills, CI workflows and Claude Code packaging** if upstream commits modify or reintroduce them:
  ```bash
  git rm -rf --ignore-unmatch \
    plugins/release-tools \
    plugins/review/skills/git-review \
    plugins/review/skills/pr \
    tests/test-release-tools.sh \
    .github/workflows \
    CLAUDE.md \
    .claude-plugin \
    'plugins/*/.claude-plugin'
  ```
- **Ported commands and agents**: AGY plugins do not load `commands/`. When upstream modifies `plugins/planning/commands/make.md`, apply the change to `plugins/planning/skills/make-plan/SKILL.md` (keep its `name`/`description` frontmatter and AGY tool names), then `git rm` the re-created `plugins/planning/commands/make.md`. Any other new upstream `plugins/*/commands/<name>.md` is ported to `plugins/*/skills/<name>/SKILL.md` the same way. When upstream modifies `plugins/*/agents/*.md`, keep the AGY markdown-agent frontmatter (`tools` as AGY tool names, `subagent: true`, `model: inherit`) and take only the body changes.
- Upstream `.claude/` project-override lookups are not used in this fork: when a merged script or test adds a `.claude/<file>` fallback, drop it and keep only `.agents/<file>`.
- If assistance is needed to resolve a conflict, use `ask_question` to confirm the resolution with the user.

### 4. Audit for Legacy Tool Leaks
After rebase completes, check if new upstream commits introduced any legacy Claude Code tool calls or paths:
```bash
grep -rn '\bBash tool\b\|\bAgent tool\b\|\bAskUserQuestion\b\|\bEnterPlanMode\b\|\bEnterWorktree\b\|\$CLAUDE_PLUGIN_ROOT\|subagent_type\|^tools: Read\|^model: opus\|via Bash' plugins/
ls -d plugins/*/commands 2>/dev/null   # must print nothing
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
