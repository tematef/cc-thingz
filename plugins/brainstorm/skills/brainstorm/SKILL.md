---
name: brainstorm
description: Use before any creative work or significant changes. Activates on "brainstorm", "let's brainstorm", "deep analysis", "analyze this feature", "think through", "help me design", "explore options for", or when user asks for thorough analysis of changes, features, or architectural decisions. Guides collaborative dialogue to turn ideas into designs through one-at-a-time questions, approach exploration, and incremental validation.
allowed-tools: view_file, write_to_file, replace_file_content, find_by_name, grep_search, run_command, invoke_subagent, ask_question
---

# Brainstorm

Turn ideas into designs through collaborative dialogue before implementation.

## custom rules loading

before starting, run this command via run_command tool to check for user-provided custom rules:

```bash
bash ~/.gemini/config/plugins/brainstorm/scripts/resolve-rules.sh brainstorm-rules.md ~/.gemini/config/plugins_data/cc-thingz
```

if the output is non-empty, treat it as additional instructions that supplement (not replace) the built-in rules below. apply custom rules alongside the skill's own instructions throughout the brainstorm process — they may influence design preferences, naming conventions, technology choices, or other aspects of the brainstorm session. custom rules content is guidance for the brainstorm dialogue, not content to embed verbatim in the output.

### rules management

when the user asks to add, show, or clear custom brainstorm rules, handle these operations:

- **show rules**: run `bash ~/.gemini/config/plugins/brainstorm/scripts/resolve-rules.sh brainstorm-rules.md ~/.gemini/config/plugins_data/cc-thingz` and display the output. if the output is empty, tell the user no custom rules are configured at either level. otherwise, to determine the source, check if `.claude/brainstorm-rules.md` exists and is non-empty (project-level) — if not, the output came from user-level. tell the user which level it came from.
- **add/update project rules**: write content to `.claude/brainstorm-rules.md` in the current working directory.
- **add/update user rules**: check if directory `~/.gemini/config/plugins_data/cc-thingz` exists (`[ -d ~/.gemini/config/plugins_data/cc-thingz ]`). if not present, offer project-level instead. if present, write content to `~/.gemini/config/plugins_data/cc-thingz/brainstorm-rules.md`.
- **clear project rules**: delete `.claude/brainstorm-rules.md`.
- **clear user rules**: delete `~/.gemini/config/plugins_data/cc-thingz/brainstorm-rules.md` if present.

project-level rules (`.claude/brainstorm-rules.md`) take precedence over user-level rules (`~/.gemini/config/plugins_data/cc-thingz/brainstorm-rules.md`). when both non-empty files exist, only project-level rules are loaded. empty files are treated as absent and fall through to the next level. see `~/.gemini/config/plugins/brainstorm/references/custom-rules.md` for full documentation on the rules mechanism.

**CRITICAL: this skill must NEVER modify its own files (skills, scripts, references, hooks, plugin.json). the ONLY files it may create or modify for rules management are `.claude/brainstorm-rules.md` and `~/.gemini/config/plugins_data/cc-thingz/brainstorm-rules.md`. if the user asks to change the skill's behavior, suggest creating a plan — do not edit skill files directly.**

## Process

### Phase 1: Understand the Idea

Check project context first, then ask questions one at a time:

1. **Gather context** - check files, docs, recent commits relevant to the idea
2. **Ask questions one at a time** - prefer multiple choice when possible
3. **Focus on**: purpose, constraints, success criteria, integration points

Do not overwhelm with multiple questions. One question per message. If a topic needs more exploration, break it into multiple questions.

### Phase 2: Explore Approaches

Once the problem is understood:

1. **Propose 2-3 different approaches** with trade-offs
2. **Lead with recommended option** and explain reasoning
3. **Present conversationally** - not a formal document yet

Example format:
```
I see three approaches:

**Option A: [name]** (recommended)
- how it works: ...
- pros: ...
- cons: ...

**Option B: [name]**
- how it works: ...
- pros: ...
- cons: ...

Which direction appeals to you?
```

### Phase 3: Present Design

After approach is selected:

1. **Break design into sections** of 200-300 words each
2. **Ask after each section** whether it looks right
3. **Cover**: architecture, components, data flow, error handling, testing
4. **Be ready to backtrack** if something doesn't make sense

Do not present entire design at once. Incremental validation catches misunderstandings early.

### Phase 4: Next Steps

After design is validated, use ask_question tool:

```json
{
  "questions": [{
    "question": "Design looks complete. What's next?",
    "header": "Next step",
    "options": [
      "Write plan - Create docs/plans/yyyymmdd-<task-name>.md with implementation steps via /planning:make",
      "Plan mode - Enter plan mode for structured implementation planning",
      "Start now - Begin implementing directly"
    ],
    "is_multi_select": false
  }]
}
```

- **Write plan**: invoke `/planning:make` command to create the plan file. Pass brainstorm context (discovered files, selected approach, design decisions) as arguments so the plan command has full context without re-asking questions
- **Plan mode**: uses write_to_file to create an implementation_plan.md artifact for detailed planning with user approval workflow
- **Start now**: proceeds directly if design is simple enough

## Key Principles

- **One question at a time** - do not overwhelm with multiple questions
- **Multiple choice preferred** - easier to answer than open-ended when possible
- **YAGNI ruthlessly** - remove unnecessary features from all designs, keep scope minimal
- **Explore alternatives** - always propose 2-3 approaches before settling
- **Incremental validation** - present design in sections, validate each
- **Be flexible** - go back and clarify when something doesn't make sense
- **Lead with recommendation** - have an opinion, explain why, but let user decide
- **Duplication vs abstraction** - when code repeats, ask user: prefer duplication (simpler, no coupling) or abstraction (DRY but adds complexity)? explain trade-offs before deciding

## Task Tracking

When implementing after brainstorm:
- Track implementation tasks using available task management tools (task lists, plan file checkboxes, or similar)
- Mark each task as completed immediately when done (do not batch)
- Keep user informed of progress through status updates
