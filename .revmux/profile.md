# Project profile: cc-thingz (AGY/Jetski fork)

## What it is

A personal fork of umputun/cc-thingz, rebuilt as native Google Antigravity (AGY) / Jetski plugins: hooks,
skills and agent prompts. There is no compiled code and no service. What ships is bash helper scripts, a
few python hook scripts, and markdown prompt files that agents read and act on.

`install.sh` registers `<repo>/plugins` in `~/.gemini/config/plugins.json` and symlinks each plugin into
`~/.gemini/config/plugins/`. Nothing is copied or versioned: a commit on `master` is live in every AGY
session the moment it lands.

## What a real failure looks like here

The scripts run unattended, inside autonomous loops nobody is watching. The failures that matter are the
ones that are silent:

- a helper that corrupts the user's git state, commits the wrong files, or loses work
- a PreToolUse hook that auto-allows a destructive command, or asks on every harmless one
- a hook that blocks the turn (no `timeout`), exits non-zero, or prints invalid JSON on bad input
- a prompt file that instructs an agent to do the wrong thing, or contradicts itself so the agent picks
  either reading
- a script that fails without saying why, or reports success after doing nothing
- a path that does not resolve once the plugin is reached through its `~/.gemini/config/plugins/` link

A crash is not the worst case. A helper that exits 0 having done something wrong is, because the loop keeps
going and the damage compounds across a run.

## Blast radius

One maintainer's machine, across every repository he opens in AGY, on his real working trees. Hooks run on
every tool call of every session, so a hook regression hits all work at once. No customer data, no
production infrastructure.

## Who runs and maintains it

Single maintainer. Upstream changes arrive only through the `cc-thingz-sync` skill. There is no remote CI:
the `tests/test-*.sh` suites, the python `--test` flags and the frontmatter check are run locally on
demand. shellcheck is not part of the toolchain.

## Reporting bar

Report anything that would make an unattended run do the wrong thing quietly, however narrow the trigger.
Report a prompt or document that would mislead an agent executing it, at the severity the wrong action
deserves, not as a documentation nit. Report hardcoded machine-specific paths, personal names or project
names in repository code.

Do not report: prose style in markdown, wording preferences, missing sections nobody asked for, or shell
constructs that work on bash 3.2 and later.

## Deliberate conventions, not defects

- `plugin.json` holds only `{"name": "cc-thingz-<plugin>"}`; there are no per-plugin versions and no
  changelog entries per change
- `hooks.json` sits at the plugin root; hook commands use paths relative to the plugin root, which AGY uses
  as the working directory. Hook names are unique across all plugins because AGY merges them by name and
  runs every handler of an event in sequence
- skills reference their helpers through `~/.gemini/config/plugins/<plugin>/...`
- per-user data lives in `~/.gemini/config/plugins_data/cc-thingz/`; project overrides live in
  `.agents/<name>-rules.md` and win over the user-level copy
- a script needed by several plugins is duplicated byte-identical in each; a test enforces it
- prompts and scripts use AGY tool names (`invoke_subagent`, `run_command`, `ask_question`, ...), never
  Claude Code ones
- python hooks target Python 3.9 (`from __future__ import annotations`)
- scripts are `#!/bin/bash` and invoked with `bash`, never `sh`
- markdown under `plugins/` is instructions for an agent, not documentation for a person. Judge it on
  whether an agent following it literally does the right thing
- subagents cannot spawn subagents, so any prompt needing parallel fan-out is executed by the main session
  rather than handed to a spawned agent
