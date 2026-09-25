# Project profile: cc-thingz (AGY/Jetski fork)

Read by revmux, not by AGY: revmux copies this file into every review round and hands it to each reviewer
agent as "the project's own conventions and standards". It calibrates what counts as a finding.

## What it is

- Personal fork of umputun/cc-thingz, rebuilt as native Google Antigravity (AGY) / Jetski plugins: hooks,
  skills, agent prompts. No compiled code, no service.
- Ships bash helper scripts, python hook scripts, and markdown prompts that agents execute literally.
- `install.sh` symlinks `plugins/*` into `~/.gemini/config/plugins/`: nothing is copied or versioned, so a
  commit on `master` is live in every AGY session immediately.

## Languages in play

- bash (`#!/bin/bash`, invoked with `bash`, must work on bash 3.2+)
- python 3.9 (`from __future__ import annotations`), stdlib only
- markdown under `plugins/` and `.agents/` = instructions for an agent, not prose for a person

## Where the rules live

- `.agents/AGENTS.md` — the project rules: plugin layout, AGY tool names, hook contracts, paths, sync,
  testing. A deviation from it is always worth reporting.
- `README.md` and `plugins/*/references/*.md` — must match behaviour (AGENTS.md §6).
- `tests/test-*.sh`, `python3 <hook>.py --test` — the only CI; run locally.

## What a real failure looks like

The scripts run unattended, inside autonomous loops nobody is watching. What matters is the silent failure:

- a helper that corrupts git state, commits the wrong files, or loses work
- a PreToolUse hook that auto-allows a destructive command, or asks on every harmless one
- a hook that blocks the turn (no `timeout`), exits non-zero, or prints invalid JSON on bad input
- a prompt that tells an agent to do the wrong thing, or contradicts itself so the agent picks either reading
- a script that fails without saying why, or reports success after doing nothing
- a path that stops resolving when the plugin is reached through its `~/.gemini/config/plugins/` link
- a hardcoded machine path, personal name or project name in repository code

A helper that exits 0 having done something wrong is worse than a crash: the loop keeps going.

## Blast radius

- One maintainer's machine, every repository he opens in AGY, his real working trees.
- Hooks run on every tool call of every session, so a hook regression hits all work at once.
- No customer data, no production infrastructure.

## Reporting bar

- Report anything that would make an unattended run do the wrong thing quietly, however narrow the trigger.
- Report a prompt or document that would mislead an agent executing it, at the severity of the wrong action.
- Do not report: markdown prose style, wording preferences, missing sections nobody asked for, shell
  constructs that work on bash 3.2+.

## Deliberate conventions, not defects

- `plugin.json` is only `{"name": "cc-thingz-<plugin>"}`: no versions, no per-change changelog entries.
- `hooks.json` sits at the plugin root; hook commands are relative to the plugin root. Hook names are
  unique across plugins because AGY runs every handler of an event in sequence.
- A script needed by several plugins is duplicated byte-identical in each; a test enforces it.
- Skills reference helpers via `~/.gemini/config/plugins/<plugin>/...`.
- `.revmux` is a symlink to `.agents/revmux`; all project agent data lives under `.agents/`.
- Subagents cannot spawn subagents, so parallel fan-out runs in the main session.
- Prompts use AGY tool names (`invoke_subagent`, `run_command`, `ask_question`), never Claude Code ones.
