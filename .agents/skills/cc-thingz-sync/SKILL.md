---
name: cc-thingz-sync
description: Syncs the local cc-thingz fork with the upstream umputun/cc-thingz repository, rebases local changes, preserves Antigravity/Jetski adaptations, and runs verification tests.
allowed-tools: run_command, view_file, write_to_file, replace_file_content, ask_question, find_by_name, grep_search
---

# cc-thingz Sync Skill

This skill pulls in updates from the original upstream repository (`https://github.com/umputun/cc-thingz.git`) and reapplies our Google Antigravity (AGY) and Jetski adaptations on top.

## Workflow

**Which remote.** "Latest" means `origin` (`tematef/cc-thingz`) by default, not upstream. For "pull/update to latest":
1. `git fetch origin`, then compare: `git rev-list --left-right --count master...origin/master`.
2. Behind only: `git merge --ff-only origin/master`.
3. Diverged (origin was force-pushed): compare tips with `git diff master origin/master --stat`. If origin already contains the local work, ask with `ask_question`, then `git branch backup/master-pre-pull-<date> master && git reset --hard origin/master`. Prefer this over `git pull` (a merge duplicates the re-recorded history) and over a rebase (which walks old commits under the live hooks, see step 3).

A tip-to-tip switch checks out one tree, so it is safe for the live hooks when `git diff master origin/master -- plugins/` is empty. Otherwise apply step 3's safeguard first.

Fetching and inspecting `upstream` is always allowed. Rebasing onto it needs the user's explicit confirmation (`.agents/AGENTS.md` §7, gated in step 3). When the user asks to sync or update `cc-thingz` from upstream, follow these steps:

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
Rebasing onto upstream needs the user's explicit confirmation (`.agents/AGENTS.md` §7). Show `git log --oneline master..upstream/master` and ask with `ask_question` before continuing; on "no", stop here.

> [!IMPORTANT]
> **Live-hook safety**: AGY loads these plugins through the `~/.gemini/config/plugins/<name>` symlinks (global discovery), which outrank the `~/.gemini/config/plugins.json` entry (global declared configuration), and both point into this checkout. A rebase checks out older commits where hook scripts (e.g. `autonomous-exec-hook.py`) may not exist, and a missing script fails AGY's live `PreToolUse` hook and blocks tool execution. Before running `git rebase`, point the symlinks at a fresh copy of the plugins:
> ```bash
> rm -rf /tmp/cc-thingz-plugins-backup && cp -R plugins /tmp/cc-thingz-plugins-backup
> for p in /tmp/cc-thingz-plugins-backup/*; do
>   [ -d "$p" ] && ln -sfn "$p" "$HOME/.gemini/config/plugins/$(basename "$p")"
> done
> ```
> The `rm -rf` first matters: if an earlier run left the directory behind, `cp -R` would nest the new copy inside it and the loop would link stale copies. `plugins.json` is not touched; `install.sh` re-registers its entry afterwards.
>
> After the rebase finishes (or is aborted), repoint the symlinks at the checkout, remove any link still pointing into the backup (plugins the rebase removed or renamed), then delete the backup:
> ```bash
> ./install.sh && {
>   for l in "$HOME"/.gemini/config/plugins/*; do
>     case "$(readlink "$l")" in /tmp/cc-thingz-plugins-backup/*) rm -f "$l" ;; esac
>   done
>   rm -rf /tmp/cc-thingz-plugins-backup
> }
> ```
> If `install.sh` fails, fix it and run the block again: until it succeeds the live links still need the backup.
>
> *Emergency rescue*: if tool execution is already blocked because a rebase checkout removed a hook script, the agent cannot write the fix itself (the `autonomous-exec-guard` hook matches every tool). Ask the **user** to create the stub by hand outside AGY, e.g. `plugins/planning/scripts/autonomous-exec-hook.py` printing `{"decision": "allow"}`. The stub is an untracked file that blocks the rebase step that restores the real script: **delete it before `git rebase --continue` and never stage it**.

Rebase current branch (typically `master`) onto `upstream/master`:
```bash
git rebase --rebase-merges upstream/master
```
`--rebase-merges` keeps the fork's merge commits (e.g. `Merge origin/master into skill-efficiency-bench`), but git does not carry over conflict resolutions made inside them: each such merge step stops again with the same conflict and must be re-resolved by hand. Enable `git config rerere.enabled true` so a resolution is recorded once and reapplied on later syncs.

If conflicts occur:
- **Do NOT overwrite AGY/Jetski adaptations**:
  - `plugin.json` in each plugin directory must remain.
  - `hooks.json` must remain at the root of `plugins/<name>/hooks.json` (not under `hooks/`).
  - `.agents/AGENTS.md` (the only rules file), `.agents/skills/` and `install.sh` must be preserved. Never let upstream reintroduce a root `AGENTS.md` or `GEMINI.md`, `.agents/CONTEXT.md` or the `.agent` symlink.
  - `.revmux/profile.md` is this fork's review profile; upstream's file at the same path describes upstream's project. During a rebase conflict on `.revmux/profile.md`, keep the fork's copy (in a `pick` step, `--theirs` is the commit being replayed) and stage it without committing:
    ```bash
    git checkout --theirs -- .revmux/profile.md && git add .revmux/profile.md
    ```
    In a `merge` step recreated by `--rebase-merges`, `--theirs` is the merged-in branch instead, so check which stage carries the fork's header before choosing: `git show :2:.revmux/profile.md | head -1` (ours) and `git show :3:.revmux/profile.md | head -1` (theirs).
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
    plugins/planning/skills/exec/scripts/run-codex.sh \
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
