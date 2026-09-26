#!/usr/bin/env bash
# Test suite for skill-bench tools (skill-audit.py, parse-transcript.py, run-bench.sh)

set -euo pipefail

SKILL_BENCH_DIR="${HOME}/.gemini/config/plugins_data/cc-thingz/skill-bench"

if [[ ! -d "$SKILL_BENCH_DIR" ]]; then
    echo "Notice: $SKILL_BENCH_DIR does not exist. Skipping skill-bench tests."
    exit 0
fi

echo "Running skill-audit.py self-tests..."
python3 "$SKILL_BENCH_DIR/skill-audit.py" --test

echo "Running parse-transcript.py self-tests..."
python3 "$SKILL_BENCH_DIR/parse-transcript.py" --test

echo "Running run-bench.sh self-tests..."
bash "$SKILL_BENCH_DIR/run-bench.sh" --test

echo "Verifying run-bench.sh --dry-run execution..."
bash "$SKILL_BENCH_DIR/run-bench.sh" --dry-run >/dev/null

echo "PASS: test-skill-bench.sh"
