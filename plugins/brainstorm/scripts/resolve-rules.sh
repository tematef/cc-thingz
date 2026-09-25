#!/bin/bash
# resolve custom rules file through the two-layer override chain
# usage: resolve-rules.sh <filename> [data-dir]
# e.g.: resolve-rules.sh brainstorm-rules.md /path/to/plugin/data
#
# data-dir: plugin data directory path, passed from SKILL.md where
# ~/.gemini/config/plugins_data/cc-thingz is text-substituted by the plugin framework.
# falls back to $GEMINI_PLUGIN_DATA env var if not provided as argument.
#
# checks in order (first-found-wins, not merged):
#   1. .agents/<filename> (project override)
#   2. <data-dir>/<filename> (user override)
#
# outputs file content to stdout if found, empty output if not
# always exits 0

filename="$1"
if [ -z "$filename" ]; then
    exit 0
fi

# use argument if provided, fall back to env var
data_dir="${2:-${GEMINI_PLUGIN_DATA:-}}"

if [ -f ".agents/$filename" ] && [ -s ".agents/$filename" ]; then
    cat ".agents/$filename"
elif [ -n "$data_dir" ] && [ -f "$data_dir/$filename" ] && [ -s "$data_dir/$filename" ]; then
    cat "$data_dir/$filename"
fi

exit 0
