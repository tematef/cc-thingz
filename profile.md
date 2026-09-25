# Project profile: cc-thingz (AGY/Jetski fork)

Review profile for [revmux](https://github.com/umputun/revmux). revmux passes it to every reviewer agent as
the project's conventions and standards, and it sets what counts as a finding. AGY does not load it as a rule.
revmux reads only `./.revmux/profile.md`, which reaches this file through the `.revmux` → `.agents/revmux`
symlink.

## What it is

- A fork of umputun/cc-thingz, rebuilt as native Google Antigravity (AGY) / Jetski plugins: hooks, skills and
  agent prompts. There is no compiled code and no service.
- It ships bash helper scripts, python hook scripts, and markdown prompts that agents execute literally.
- `install.sh` symlinks `plugins/*` into `~/.gemini/config/plugins/`. Nothing is copied or versioned, so a
  commit is live in every AGY session of whoever installed it from that checkout.

## Languages in play

- bash (`#!/bin/bash`, invoked with `bash`, must work on bash 3.2+)
- python 3.9 (`from __future__ import annotations`), stdlib only
- markdown under `plugins/` and `.agents/`: instructions for an agent, not prose for a person

## Where the rules live

- `.agents/AGENTS.md` holds the project rules: plugin layout, AGY tool names, hook contracts, paths, upstream
  sync and testing. A deviation from it is always worth reporting.
- `README.md` and `plugins/*/references/*.md` must match behaviour.
- The tests are `tests/test-*.sh` and `python3 <hook>.py --test`. There is no remote CI; checks run locally.

## What a real failure looks like

The scripts run unattended, inside autonomous loops nobody is watching. The failures that matter are the
silent ones:

- a helper that corrupts git state, commits the wrong files, or loses work
- a PreToolUse hook that auto-allows a destructive command, or asks on every harmless one
- a hook that blocks the turn (no `timeout`), exits non-zero, or prints invalid JSON on bad input
- a prompt that tells an agent to do the wrong thing, or contradicts itself so the agent picks either reading
- a script that fails without saying why, or reports success after doing nothing
- a path that stops resolving when the plugin is reached through its `~/.gemini/config/plugins/` link
- a hardcoded machine-specific path, user name or project name in repository code

A helper that exits 0 having done something wrong is worse than a crash, because the loop keeps going.

## Blast radius

- Every workstation where the plugins are installed, across every repository opened in AGY there, on real
  working trees.
- Hooks run on every tool call of every session, so a hook regression breaks all work at once.
- No customer data and no production infrastructure are involved.

## Reporting bar

- Report anything that would make an unattended run do the wrong thing quietly, however narrow the trigger.
- Report a prompt or document that would mislead an agent executing it, at the severity the wrong action
  deserves.
- Do not report markdown prose style, wording preferences, missing sections nobody asked for, or shell
  constructs that work on bash 3.2+.

## Deliberate conventions, not defects

- `plugin.json` is only `{"name": "cc-thingz-<plugin>"}`: no versions and no per-change changelog entries.
- `hooks.json` sits at the plugin root, and hook commands are relative to the plugin root. Hook names are
  unique across plugins because AGY runs every handler of an event in sequence.
- A script needed by several plugins is duplicated byte-identical in each; a test enforces it.
- Skills reference helpers via `~/.gemini/config/plugins/<plugin>/...`.
- Per-user data lives in `~/.gemini/config/plugins_data/cc-thingz/`, and project overrides in `.agents/`.
- Subagents cannot spawn subagents, so parallel fan-out runs in the main session.
- Prompts use AGY tool names (`invoke_subagent`, `run_command`, `ask_question`), never Claude Code ones.
