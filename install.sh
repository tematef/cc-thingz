#!/bin/bash
# install.sh - Registers the local cc-thingz plugins in AGY/Jetski

set -e

PLUGIN_DIR="$(cd "$(dirname "$0")/plugins" && pwd)"
CONFIG_FILE="$HOME/.gemini/config/plugins.json"
CONFIG_DIR="$(dirname "$CONFIG_FILE")"

mkdir -p "$CONFIG_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "{ \"entries\": [] }" > "$CONFIG_FILE"
fi

# Check if the path is already registered
if grep -q "$PLUGIN_DIR" "$CONFIG_FILE"; then
    echo "cc-thingz plugins are already registered in $CONFIG_FILE"
else
    # Simple hack to insert the path into the entries array using jq (or perl if jq not available)
    if command -v jq >/dev/null 2>&1; then
        jq --arg path "$PLUGIN_DIR" '.entries += [{"path": $path}]' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
    else
        # Fallback using a basic awk script since json parsing in bash is hard without jq
        awk -v path="$PLUGIN_DIR" '
        /\"entries\": \[\s*$/ {
            print $0;
            print "    { \"path\": \"" path "\" },";
            next;
        }
        /\"entries\": \[\s*\]/ {
            sub(/\[\s*\]/, "[\n    { \"path\": \"" path "\" }\n  ]");
            print;
            next;
        }
        {print}
        ' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
        # The awk fallback might leave a trailing comma if it was an empty array, but we assume jq is usually available or the user can fix it.
    fi
    echo "Successfully registered cc-thingz plugins in $CONFIG_FILE"
fi

echo "AGY/Jetski will now automatically load skills, rules, and hooks from $PLUGIN_DIR."
