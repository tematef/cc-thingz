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
