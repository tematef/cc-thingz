# Repository Context

This repository is a fork of [umputun/cc-thingz](https://github.com/umputun/cc-thingz), explicitly adapted to support **Google Antigravity (AGY)** and its corporate clone, **Jetski**.

## Guidelines for Agents Working Here

When contributing to this repository, you must adhere to the following rules:

1. **Plugin Architecture:** 
   The `plugins/` directory uses the native AGY/Jetski Plugin Bundle format. 
   - Each plugin directory must contain a `plugin.json` manifest.
   - `hooks.json` files must reside at the root of a plugin directory to be automatically ingested. Do not nest them under `hooks/`.

2. **Tool Usage in Prompts:** 
   When writing or modifying skills (`SKILL.md`), scripts, or prompts, you MUST use AGY/Jetski tool syntax instead of Claude Code tools:
   - Use `invoke_subagent` instead of `Agent`.
   - Use `run_command` instead of `Bash`.
   - Use `ask_question` instead of `AskUserQuestion`. Ensure the payload matches AGY schema (`options` as string array, `is_multi_select`).
   - Use `view_file`, `write_to_file`, `replace_file_content` instead of `Read`, `Write`, `Edit`.

3. **Hook Scripts:** 
   Any lifecycle hook scripts (Python or Bash) must be written for the AGY ecosystem:
   - Read the payload from `stdin` as a JSON object (uses `camelCase` keys like `conversationId`, `stepIdx`, `artifactDirectoryPath`).
   - Output a strictly formatted JSON object to `stdout` (e.g., `{"decision": "continue", "reason": "..."}` for `Stop` hooks, or `{"injectSteps": [...]}` for `PreInvocation` hooks).

4. **Detailed Tool & Plugin Context:**
   For a comprehensive architectural breakdown of the tool suite, available plugins, and workflow capabilities, see [.agents/CONTEXT.md](file:///Users/artem/projects/cc-thingz/.agents/CONTEXT.md).

5. **Upstream Synchronization:**
   To synchronize this fork with upstream updates from `umputun/cc-thingz`, use the `cc-thingz-sync` skill (`.agent/skills/cc-thingz-sync/SKILL.md`). Always ensure our AGY/Jetski adaptations are preserved during rebase conflicts and discard excluded upstream skills.

6. **Subagent Orchestration Constraints:**
   - Subagents do not have `invoke_subagent` tool access (no recursive nesting).
   - Any multi-agent fanout (such as `plugins/planning/skills/exec/references/prompts/review.md`) must be executed directly by the main session orchestrator as a playbook rather than delegated to a child subagent.
   - Single-subagent prompts perform leaf tasks only (`prompts/task.md`, `prompts/fixer.md`, `prompts/finalizer.md`, `agents/smells.txt`).

7. **Generic Configuration & Documentation Integrity:**
   - Never hardcode personal paths, machine-specific directories, or private settings. Use environment variables or AGY user-level data directory (`~/.gemini/config/plugins_data/cc-thingz/`).
   - Keep `README.md` and plugin reference documentation synchronized whenever skills, tools, or workflows are added or modified.

8. **Testing & Verification:**
   - Run all shell test suites: `for t in tests/test-*.sh; do bash "$t"; done`
   - Validate YAML frontmatter across all skills: `python3 .github/scripts/check-frontmatter.py .`
   - Run embedded tests in Python scripts where available: `python3 <script> --test`

9. **No Remote CI / GitHub Actions:**
   - This repository does not use GitHub Actions or remote CI workflows (`.github/workflows/` must remain deleted).
   - All linting, tests, and verifications are executed locally on demand.
   - When synchronizing with upstream using `cc-thingz-sync`, discard any incoming `.github/workflows/` files.

10. **Excluded Upstream Plugins & Skills (Never Re-import on Sync):**
    - `plugins/release-tools/` (`last-tag`, `new`), `plugins/review/skills/git-review/`, `plugins/review/skills/pr/`, and `tests/test-release-tools.sh` are intentionally removed from this fork (`revmux` supersedes `git-review` and `pr`).
    - When synchronizing with `umputun/cc-thingz`, always discard (`git rm -rf --ignore-unmatch`) any incoming files under `plugins/release-tools/`, `plugins/review/skills/git-review/`, `plugins/review/skills/pr/`, and `tests/test-release-tools.sh`.


