# AGENTS.md

Project rules for Google Antigravity (AGY) and Jetski agents working in this repository.
This file (`.agents/AGENTS.md`, discovered by AGY in the `.agents/` directory) is the only rules file here — do not add a root `AGENTS.md`, `GEMINI.md` or `CLAUDE.md`.

## Purpose

This repository is a fork of [umputun/cc-thingz](https://github.com/umputun/cc-thingz), rebuilt as a native plugin suite for **AGY / Jetski**: planning, brainstorm, review, thinking tools, workflow helpers and skill evaluation.
The plugin catalog and the architecture diagrams live in [README.md](README.md).

## 1. Plugin architecture

Every plugin under `plugins/` is a native AGY plugin bundle:

```text
plugins/<plugin-name>/
├── plugin.json       # manifest: {"name": "cc-thingz-<plugin-name>"}
├── hooks.json        # lifecycle hooks — MUST sit at the plugin root, never under hooks/
├── scripts/          # helper scripts
├── references/       # docs the skills read on demand
└── skills/<skill>/SKILL.md
```

- `hooks.json` handlers run with the plugin root as working directory, so script paths in `command` are relative to it.
- A script needed by more than one plugin is shipped **byte-identical** in each (e.g. `resolve-project-dir.sh`); a test fails if the copies drift.

## 2. AGY tool names

Skills, prompts and scripts use AGY tool names, never Claude Code ones:

| Claude Code             | AGY / Jetski                                        | Notes                                                                                |
| :---------------------- | :-------------------------------------------------- | :----------------------------------------------------------------------------------- |
| `Agent` / `Task`        | `invoke_subagent`                                   | `Subagents: [{"TypeName": "self", "Role": "...", "Prompt": "..."}]`                  |
| `Bash`                  | `run_command`                                       | `CommandLine`, `Cwd`, `WaitMsBeforeAsync`                                            |
| `AskUserQuestion`       | `ask_question`                                      | `options` is a flat array of strings; `is_multi_select` is a boolean                 |
| `Read`, `Write`, `Edit` | `view_file`, `write_to_file`, `replace_file_content` |                                                                                     |
| `Glob`, `Grep`          | `find_by_name`, `grep_search`                       |                                                                                      |
| `EnterPlanMode`         | artifact                                            | write `<appDataDir>/brain/<conversation-id>/implementation_plan.md`                  |

## 3. Lifecycle hooks

- Handlers read a JSON payload on `stdin` (`camelCase` keys: `conversationId`, `workspacePaths`, `artifactDirectoryPath`, `stepIdx`, …) and print one JSON object on `stdout`.
- `PreToolUse` → `{"decision": "allow" | "ask" | "deny" | "force_ask"}`; tool events use the grouped form (`matcher` + `hooks`).
- `PreInvocation` → `{}` or `{"injectSteps": [{"ephemeralMessage": "..."}]}`; flat handler list.
- `Stop` → `{"decision": "allow"}` or `{"decision": "continue", "reason": "..."}`; flat handler list.
- AGY merges the hooks of all plugins and runs the handlers of one event **in sequence** — they do not override each other. Hook names are keys, so every name must be **unique across all plugins**.
- A hook blocks the agent turn while it runs: set a `timeout`, and on bad input or internal errors still exit 0 with valid JSON.
- `tests/test-hooks-json.sh` enforces placement, unique names, event form, referenced scripts and output shape.

## 4. Subagent orchestration

- Subagents have no `invoke_subagent` (no recursive nesting).
- Multi-agent fan-out (e.g. `plugins/planning/skills/exec/references/prompts/review.md`) runs in the main session as a playbook, never delegated to a child subagent.
- Single-subagent prompts are leaf tasks only: `prompts/task.md`, `prompts/fixer.md`, `prompts/finalizer.md`, `agents/smells.txt`.

## 5. Paths, config and custom rules

- AGY config lives in `~/.gemini/config/`; `./install.sh` registers the plugins in `~/.gemini/config/plugins.json` (plugins are linked, so edits here take effect immediately).
- Per-user plugin data: `~/.gemini/config/plugins_data/cc-thingz/`.
- Project-level custom rules: `.agents/<name>-rules.md` (e.g. `.agents/planning-rules.md`, `.agents/brainstorm-rules.md`); they take precedence over the user-level copy in the data directory.
- Project agent data lives under `.agents/`:
  - `.agents/AGENTS.md` — this rules file;
  - `.agents/skills/` — project-only skills (`cc-thingz-sync`);
  - `.agents/<name>-rules.md` — project rules for the planning and brainstorm plugins;
- revmux data stays in its native `.revmux/`, because revmux reads only `./.revmux/profile.md` (relative to where it is started) and no flag relocates it:
  - `.revmux/profile.md` — the review profile revmux gives every reviewer agent. Keep it generic: no user-, machine- or instance-specific details;
  - `.revmux/tasks/` — review round archives (gitignored).
- Never hardcode machine-specific paths, personal settings or project names; use environment variables, the data directory, or resolve at runtime (`resolve-project-dir.sh`).

## 6. Documentation integrity

- Keep `README.md` and the plugin `references/` docs in sync with every added or changed skill, hook or workflow.

## 7. Upstream synchronization

- Sync with `https://github.com/umputun/cc-thingz.git` only through the `cc-thingz-sync` skill (`.agents/skills/cc-thingz-sync/SKILL.md`); it preserves the AGY/Jetski adaptations during the rebase.
- **Never re-import** (always `git rm -rf --ignore-unmatch` when upstream touches them):
  - `plugins/release-tools/` (`last-tag`, `new`), `plugins/review/skills/git-review/`, `plugins/review/skills/pr/`, `tests/test-release-tools.sh` — `revmux` replaces `git-review` and `pr`;
  - `.github/workflows/`;
  - Claude Code packaging: `CLAUDE.md`, `.claude-plugin/`, `plugins/*/.claude-plugin/`.
- **Keep ours for `.revmux/profile.md`**: upstream's copy describes upstream's project. When upstream touches it, keep the fork's version.

## 8. No remote CI

- No GitHub Actions: `.github/workflows/` must not exist. All checks run locally on demand.

## 9. Testing

```bash
for t in tests/test-*.sh; do bash "$t" || echo "FAIL: $t"; done       # all shell suites
python3 plugins/planning/scripts/autonomous-exec-hook.py --test         # embedded tests
python3 plugins/planning/scripts/ralphex-plans-link-hook.py --test
python3 .github/scripts/check-frontmatter.py .                          # needs PyYAML
```

Python hooks must stay compatible with Python 3.9 (`from __future__ import annotations`).
