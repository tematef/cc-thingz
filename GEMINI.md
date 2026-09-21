# GEMINI.md

This file provides project guidance and conventions to Google Antigravity (AGY) and Jetski agents operating in this repository.

## Repository Purpose

This repository is an adapted fork of [umputun/cc-thingz](https://github.com/umputun/cc-thingz), specifically rebuilt to provide a native plugin suite (planning, review, release tools, thinking tools, brainstorm, workflow, skill evaluation) for **Google Antigravity (AGY)** and its corporate clone, **Jetski**.

## Key Rules & Guidelines

1. **Plugin Architecture:**
   - Every plugin under `plugins/` adheres to the native AGY Plugin Bundle format.
   - Each plugin directory contains a `plugin.json` manifest.
   - Any `hooks.json` file must reside at the root of its plugin directory (e.g. `plugins/planning/hooks.json`), never nested in a `hooks/` subfolder.

2. **Tool Usage:**
   - Always use AGY tool signatures instead of Claude Code tools:
     - `invoke_subagent` instead of `Agent` / `Task`.
     - `run_command` instead of `Bash`.
     - `ask_question` instead of `AskUserQuestion` (with flat string arrays for `options`).
     - `view_file`, `write_to_file`, `replace_file_content` instead of `Read`, `Write`, `Edit`.
     - `find_by_name`, `grep_search` instead of `Glob`, `Grep`.

3. **Lifecycle Hooks:**
   - Hook scripts receive JSON payloads via `stdin` (`camelCase` keys like `conversationId`, `artifactDirectoryPath`).
   - `Stop` hooks output `{"decision": "allow"}` or `{"decision": "continue", "reason": "..."}` to force agent revision.
   - `PreInvocation` hooks output `{"injectSteps": [{"ephemeralMessage": "..."}]}`.

4. **Rules & Memory Files:**
   - Agent guidance is maintained in `GEMINI.md` and `AGENTS.md` (or `.agents/AGENTS.md`).
   - Project-level rules live in `.agents/` (e.g., `.agents/planning-rules.md`, `.agents/brainstorm-rules.md`).
   - User-level persistent data lives in `~/.gemini/config/plugins_data/cc-thingz/`.

5. **Upstream Synchronization:**
   - Use the `cc-thingz-sync` skill (`.agent/skills/cc-thingz-sync/SKILL.md`) to rebase changes against `https://github.com/umputun/cc-thingz.git` while preserving AGY/Jetski adaptations and discarding excluded upstream skills.

6. **Subagent Orchestration Constraints:**
   - Subagents do not have `invoke_subagent` tool access.
   - Any multi-agent fanout (e.g. `plugins/planning/skills/exec/references/prompts/review.md`) must be executed directly by the main session orchestrator as a playbook rather than delegated to a child subagent.
   - Single-subagent prompts perform leaf tasks only (`prompts/task.md`, `prompts/fixer.md`, `prompts/finalizer.md`, `agents/smells.txt`).

7. **Generic Configuration & Documentation:**
   - Never hardcode machine-specific paths or personal settings.
   - Keep `README.md` updated with every new or modified tool/workflow.

8. **No Remote CI Workflows:**
   - Do not create or reintroduce GitHub Actions workflow files under `.github/workflows/`.
   - All tests and validation run locally (`tests/test-*.sh`, `python3 .github/scripts/check-frontmatter.py .`).
   - Discard any upstream `.github/workflows/` files during sync.

9. **Excluded Upstream Plugins & Skills (Never Re-import on Sync):**
   - `plugins/release-tools/` (`last-tag`, `new`), `plugins/review/skills/git-review/`, `plugins/review/skills/pr/`, and `tests/test-release-tools.sh` are permanently removed from this fork (`revmux` replaces `git-review` and `pr`).
   - Always discard (`git rm -rf --ignore-unmatch`) these paths if upstream commits touch or reintroduce them during `cc-thingz-sync`.

## Testing

- Shell test scripts live in `tests/`: `for t in tests/test-*.sh; do bash "$t"; done`
- Python hook scripts include embedded tests where applicable: `python3 <script> --test`
- YAML frontmatter validation: `python3 .github/scripts/check-frontmatter.py .`
