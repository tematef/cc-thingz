#!/bin/bash
# initialize the progress file with a header
# usage: init-progress.sh <progress-file> <plan-path> <branch-name>

set -e

file="$1"
plan="$2"
branch="$3"

if [ -z "$file" ] || [ -z "$plan" ] || [ -z "$branch" ]; then
    echo "error: usage: init-progress.sh <progress-file> <plan-path> <branch-name>" >&2
    exit 1
fi

cat > "$file" <<EOF
# progress
Plan: $plan
Branch: $branch
Started: $(date '+%Y-%m-%d %H:%M:%S')
---
EOF

MARKER_DIR="$HOME/.gemini/config/plugins_data/cc-thingz"
mkdir -p "$MARKER_DIR" 2>/dev/null || true
pwd -P > "$MARKER_DIR/autonomous-active" 2>/dev/null || true

echo "$file"
