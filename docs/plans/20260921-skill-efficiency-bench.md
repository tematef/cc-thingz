# Skill Efficiency Benchmarking Suite

## Overview
Build a two-part tooling suite to measure and optimize the efficiency of AGY/Jetski custom skills:
- **Part B: Static Skill Audit** — scans all skill sources, measures size/tokens, detects duplicates, reports overhead
- **Part A: Transcript-Based Benchmarking** — parses `transcript.jsonl` files to extract performance metrics (TTFT, tokens, steps, wall-clock time)

**Problem**: 38+ skills totaling ~259 KB of SKILL.md text are loaded across project and user levels. Many are duplicated at both levels. This increases time-to-first-token, total token consumption, and potentially degrades decision quality.

**Acceptance criteria**:
- `skill-audit.py` discovers all skill sources (project plugins, .agent, .agents, skills/, user plugins, user skills, extensions, builtins), reports size leaderboard, detects duplicates, summarizes total overhead
- `parse-transcript.py` extracts TTFT, total tokens (estimated), step count, tool call count, wall-clock time, and skill activation from `transcript.jsonl` files
- Both scripts produce clean markdown reports
- Scripts live in `~/.gemini/config/plugins_data/cc-thingz/skill-bench/` for cross-project availability

## Context (from brainstorm discovery)

### Current skill landscape
- **Project-level** (`plugins/`, `.agent/skills/`): 17 SKILL.md files, ~105 KB total
- **User-level** (`~/.gemini/config/plugins/`, `~/.gemini/config/skills/`): 21 SKILL.md files, ~154 KB total
- **Extensions** (`~/.gemini/extensions/`): 5 more skills (chrome-devtools-mcp)
- **Builtins** (`~/.gemini/antigravity-cli/builtin/skills/`): 5 builtin skills
- **Biggest offenders**: `revmux` (46 KB), `exec` (31 KB × 2 duplicated), `backlog` (13 KB × 2)
- Additional context: AGENTS.md (4 KB), GEMINI.md (4 KB), .agents/CONTEXT.md (5.6 KB), hooks

### Transcript format
- Located at `~/.gemini/antigravity-cli/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`
- JSONL format with fields: `step_index`, `source`, `type`, `status`, `created_at`, `content`, `tool_calls`
- Key step types: `USER_INPUT`, `PLANNER_RESPONSE`
- Timestamps are ISO 8601

### Discovery paths for audit (all tiers)
| Tier | Pattern |
|------|---------|
| Project plugins | `<project>/plugins/*/skills/*/SKILL.md` |
| Project .agent | `<project>/.agent/skills/*/SKILL.md` |
| Project .agents | `<project>/.agents/skills/*/SKILL.md` |
| Project skills/ | `<project>/skills/*/SKILL.md` |
| User plugins | `~/.gemini/config/plugins/*/skills/*/SKILL.md` |
| User skills | `~/.gemini/config/skills/*/SKILL.md` |
| Extensions | `~/.gemini/extensions/*/skills/*/SKILL.md` |
| Builtins | `~/.gemini/antigravity-cli/builtin/skills/*/SKILL.md` |

### Key metrics to extract from transcripts
| Metric | Derivation | Purpose |
|--------|-----------|---------|
| TTFT | First `PLANNER_RESPONSE` created_at − `USER_INPUT` created_at | Latency |
| Input tokens (est.) | System prompt + user content bytes ÷ 4 | Prompt cost |
| Output tokens (est.) | Model output content bytes ÷ 4 | Generation cost |
| Step count | Count of `PLANNER_RESPONSE` steps | Roundtrip overhead |
| Tool call count | Sum of tool_calls arrays across all steps | Efficiency |
| Wall-clock time | Last step created_at − first step created_at | End-to-end UX |
| Skill activation | Skill name found in system prompt or tool calls | Routing accuracy |

## Development Approach
- Python 3 with no external dependencies (stdlib only: json, os, pathlib, hashlib, datetime, argparse)
- Complete each task fully before moving to the next
- Run `python3 <script> --test` where embedded tests are provided
- Reports output as markdown to stdout, optionally saved to reports/ directory

## Progress Tracking
- Mark completed items with `[x]` immediately when done
- Add newly discovered tasks with ➕ prefix
- Document issues/blockers with ⚠️ prefix

---

### Task 1: Create skill-audit.py — Static Skill Discovery & Analysis

**File**: `~/.gemini/config/plugins_data/cc-thingz/skill-bench/skill-audit.py`

Build a Python script that:

1. **Accepts arguments**:
   - `--project <path>` — project root (defaults to current directory)
   - `--user-home <path>` — user home (defaults to `~`)
   - `--output <path>` — optional file path for report (defaults to stdout)
   - `--test` — run embedded self-tests

2. **Discovers skills** from all 8 tiers listed in Context above. For each skill found, record:
   - Skill name (directory name containing SKILL.md)
   - Full path
   - Tier (project-plugin, project-agent, user-plugin, user-skill, extension, builtin)
   - File size in bytes
   - Estimated token count (bytes ÷ 4)
   - Content hash (SHA-256 of file content)

3. **Detects duplicates**: Group skills by name, flag groups where the same skill name appears at multiple tiers. Within each group, compare content hashes to identify identical vs. divergent copies.

4. **Generates markdown report** with sections:
   - **Summary**: Total skills count, total bytes, estimated total tokens, duplicate count
   - **Size Leaderboard**: All skills sorted by size (descending), with tier label and size. Flag skills > 10 KB as "⚠️ heavy"
   - **Duplicate Report**: Skills found at multiple tiers, showing which copies are identical (same hash) vs. divergent (different hash). For identical copies, recommend keeping only one level.
   - **Tier Breakdown**: Bytes and skill count per tier
   - **Overhead Context**: Compare total skill tokens to a baseline (AGENTS.md + GEMINI.md sizes)

5. **Embedded tests** (`--test`): Create temp directories with mock SKILL.md files across tiers, run discovery, verify counts, duplicate detection, and report generation.

- [x] complete

---

### Task 2: Create parse-transcript.py — Transcript Metrics Extraction

**File**: `~/.gemini/config/plugins_data/cc-thingz/skill-bench/parse-transcript.py`

Build a Python script that:

1. **Accepts arguments**:
   - `<transcript_paths>` — one or more paths to `transcript.jsonl` files, or directories containing them (will recursively find `transcript.jsonl` files)
   - `--output <path>` — optional file path for report
   - `--compare <path>` — optional second set of transcripts for A/B comparison
   - `--test` — run embedded self-tests

2. **Parses each transcript.jsonl** and extracts per-conversation metrics:
   - Conversation ID (from directory path)
   - First user prompt text (truncated to 80 chars for identification)
   - TTFT: timestamp delta between first `USER_INPUT` and first `PLANNER_RESPONSE`
   - Total estimated input tokens: sum of `content` byte lengths for USER_INPUT and SYSTEM source steps, ÷ 4
   - Total estimated output tokens: sum of `content` byte lengths for PLANNER_RESPONSE steps, ÷ 4
   - Step count: number of PLANNER_RESPONSE steps
   - Tool call count: total tool_calls entries across all steps
   - Wall-clock time: last step created_at − first step created_at
   - Skills mentioned: scan content and tool_calls for known skill names

3. **Single-set report**: Markdown table of all conversations sorted by wall-clock time (descending), with summary stats (mean, median, p95 for each metric).

4. **Comparison report** (when `--compare` is used): Side-by-side table showing Set A vs Set B metrics, with delta percentages. Highlights improvements (green ✅) and regressions (red ❌).

5. **Embedded tests** (`--test`): Create mock transcript.jsonl files with known metrics, verify extraction accuracy.

- [x] complete

---

### Task 3: Create benchmark-prompts.json — Test Prompt Bank

**File**: `~/.gemini/config/plugins_data/cc-thingz/skill-bench/benchmark-prompts.json`

Create a JSON file with 6-8 representative test prompts:

```json
[
  {
    "id": "baseline-simple",
    "prompt": "What does the main function in this project do?",
    "expected_skills": [],
    "category": "baseline",
    "description": "Simple question that should NOT activate any skill — measures pure overhead"
  },
  {
    "id": "review-trigger",
    "prompt": "Review the last commit for code quality issues",
    "expected_skills": ["git-review", "code-review-best-practices"],
    "category": "review",
    "description": "Should activate review skills"
  }
]
```

Each prompt has:
- `id` — unique identifier
- `prompt` — the exact text to send to AGY
- `expected_skills` — which skills should activate (for routing accuracy)
- `category` — grouping for report
- `description` — what this tests

Include prompts for: baseline (no skill), review, brainstorm, planning/exec, code refactor, and a "confusing" prompt that might misroute.

- [x] complete

---

### Task 4: Create run-bench.sh — Benchmark Runner Script

**File**: `~/.gemini/config/plugins_data/cc-thingz/skill-bench/run-bench.sh`

Create a bash script that:

1. **Reads** `benchmark-prompts.json` and iterates over prompts
2. **For each prompt**, records the transcript directory path before and after running `agy` (or documents the manual process if headless mode isn't available)
3. **Collects** transcript paths into a results manifest file
4. **Invokes** `parse-transcript.py` on the collected transcripts to generate the benchmark report
5. **Supports flags**:
   - `--dry-run` — prints what it would do without running AGY
   - `--manual` — prints prompts for the user to manually run, then collects transcript paths interactively
   - `--label <name>` — names this benchmark run for comparison

The script should document clearly how to run a comparison:
```bash
# Run with full skills
./run-bench.sh --label full-skills
# Disable project plugins, run again
./run-bench.sh --label minimal
# Compare
python3 parse-transcript.py reports/full-skills/ --compare reports/minimal/
```

- [ ] complete

---

### Task 5: Create README.md — Usage Documentation

**File**: `~/.gemini/config/plugins_data/cc-thingz/skill-bench/README.md`

Write documentation covering:
- What the suite does and why
- Quick start: run `skill-audit.py` first, then benchmark
- Full command reference for each script
- How to interpret the reports
- Recommended workflow: audit → prune → benchmark → compare → iterate
- Example output snippets

- [ ] complete

---

### Task 6: Run Initial Audit & Report

Run `skill-audit.py` against the current project and user setup to produce the first audit report. Save the report to `reports/audit-20260921.md`. Review findings and note actionable items (duplicates to remove, heavy skills to trim).

- [ ] complete
