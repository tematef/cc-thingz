# cc-thingz (AGY & Jetski Edition) — Tool & Architecture Context

## Overview

This repository is an adapted fork of [umputun/cc-thingz](https://github.com/umputun/cc-thingz), an opinionated suite of developer plugins and skills for agentic pair-programming. While the original upstream repository was authored for Claude Code and Codex, this fork has been restructured and rewritten to natively support **Google Antigravity 2.0 (AGY)** and its enterprise variant, **Jetski**.

---

## Purpose & Capabilities

`cc-thingz` extends the AI assistant with specialized subagents, multi-stage review loops, interactive TUI hooks, and workflow automations:

### 1. Planning (`plugins/planning`)
- **`/planning:make`**: Interactive requirements elicitation and structured plan creation in the project's `docs/plans/` (resolved by `scripts/resolve-project-dir.sh` from the working directory, so monorepo sub-projects keep their own `docs/plans/` and `completed/`).
- **`/planning:exec`**: Autonomous, sequential plan execution where each task runs in an isolated `invoke_subagent` instance, followed by multi-phase code reviews (comprehensive, smells, external, critical-only), commit finalization, and session stats summaries.
- **`plan-review-hook.py`**: Intercepts the agent turn via AGY's `Stop` lifecycle hook. When an `implementation_plan.md` artifact is created or modified, it opens an interactive visual diff in `revdiff` (or editor fallback) for user line-by-line annotations before execution begins. State is tracked via SHA-256 hashes (`.plan_reviewed.hash`) to avoid redundant review prompts.

### 2. Brainstorming (`plugins/brainstorm`)
- **`/brainstorm`**: Guided exploration and design dialogue before code is written. Integrates project- and user-level custom rules (`resolve-rules.sh`).

### 3. Review (`plugins/review`)
- **`/review:git-review`**: Automated multi-agent review over local branch diffs, integrating `revdiff` annotations.
- **`/review:pr`**: Deep pull request reviews analyzing intent, test coverage, and regressions.

### 4. Release Tools (`plugins/release-tools`)
- **`/release-tools:new`**: Automates semantic release tagging, forge platform detection (GitHub, GitLab, Gitea), and generates categorized release notes from commit histories and merged PRs.
- **`/release-tools:last-tag`**: Summarizes commit activity, churn, and changes since the latest release tag.

### 5. Thinking Tools (`plugins/thinking-tools`)
- **`/thinking-tools:dialectic`**: Launches thesis and antithesis subagents in parallel to debate complex architectural decisions.
- **`/thinking-tools:ask-codex`**: Delegates deep reasoning or cross-model analysis to external CLI models in the background.

### 6. Workflow & Maintenance (`plugins/workflow`)
- **`/workflow:learn`**: Extracts reusable project conventions and patterns from conversation trajectories and records them in documentation.
- **`/workflow:clarify`**: Analyzes developer confusion, determines whether it stems from documentation, configuration, or genuine software defects, and routes to planning.
- **`/workflow:backlog`**: Tracks deferred technical debt and non-blocking improvement items in the project's `docs/backlog/`; closed items are archived to `docs/backlog/completed/` with `closed`/`outcome` frontmatter.
- **`/workflow:wrong`**: Adversarial assumption tester that identifies logical fallacies or architectural blindspots.
- **`/workflow:sync` (`cc-thingz-sync`)**: Syncs and rebases this fork against upstream `umputun/cc-thingz` while preserving AGY/Jetski adaptations.

### 7. Skill Evaluation (`plugins/skill-eval`)
- **`skill-forced-eval-hook.sh`**: AGY `PreInvocation` hook that injects ephemeral instructions prompting the model to evaluate and view relevant `SKILL.md` files before generating code.

---

## Architectural Conventions for AGY & Jetski

When adding, editing, or maintaining skills in this repository, follow these conventions:

### Native Plugin Bundle Layout
Every plugin under `plugins/` adheres to AGY's native bundle format:
```text
plugins/<plugin-name>/
├── plugin.json       # Manifest declaring plugin name
├── hooks.json        # Lifecycle hooks (MUST reside at plugin root, not in hooks/)
├── rules/            # Plugin-scoped rules (optional)
├── scripts/          # Helper scripts and tools
└── skills/           # Bundled skills
    └── <skill-name>/
        └── SKILL.md
```

### Tool Usage Semantics
Always use AGY tool signatures instead of Claude Code tools:
| Claude Code Tool | AGY / Jetski Tool Equivalent | Notes |
|---|---|---|
| `Agent(...)` | `invoke_subagent(...)` | Pass `Subagents: [{"TypeName": "self", "Role": "...", "Prompt": "..."}]` |
| `Bash(...)` | `run_command(...)` | Pass `CommandLine`, `Cwd`, and `WaitMsBeforeAsync` |
| `AskUserQuestion(...)` | `ask_question(...)` | `options` MUST be flat array of strings (`["Opt 1 - Desc", "Opt 2"]`), `is_multi_select` boolean |
| `Read`, `Write`, `Edit` | `view_file`, `write_to_file`, `replace_file_content` | Standard file operations |
| `Glob`, `Grep` | `find_by_name`, `grep_search` | Workspace search |
| `EnterPlanMode` | Artifact generation | Create `<appDataDir>/brain/<id>/implementation_plan.md` |

### Lifecycle Hooks Contract
Hook scripts receive JSON context over `stdin` (`camelCase` keys like `conversationId`, `artifactDirectoryPath`) and emit formatted JSON to `stdout`:
- **`Stop` hooks**: Return `{"decision": "allow"}` or `{"decision": "continue", "reason": "..."}` to force agent revision.
- **`PreInvocation` hooks**: Return `{"injectSteps": [{"ephemeralMessage": "..."}]}`.

### Environment & Paths
- Config files reside in `~/.gemini/config/` (never `~/.claude/`).
- Persistent plugin data resides in `~/.gemini/config/plugins_data/cc-thingz/`.
- Discovery is managed via `~/.gemini/config/plugins.json`. Run `./install.sh` to register the local repository.
