#!/bin/bash
# uninstall-keymap.sh — Remove the "Open in IDE" command from agterm's keymap.conf.
#
# Identifies the line by the MARKER comment and removes it, then reloads the keymap.

set -euo pipefail

KEYMAP="$HOME/.config/agterm/keymap.conf"
MARKER="# cc-thingz:agterm-ide-launcher"

if [ -f "$KEYMAP" ] && grep -q "$MARKER" "$KEYMAP"; then
    grep -v "$MARKER" "$KEYMAP" > "${KEYMAP}.tmp" && mv "${KEYMAP}.tmp" "$KEYMAP"
    # collapse duplicate blank lines left behind
    awk 'NF || !blank++; NF{blank=0}' "$KEYMAP" > "${KEYMAP}.tmp" && mv "${KEYMAP}.tmp" "$KEYMAP"
    agtermctl keymap reload 2>/dev/null || true
    echo "✓ Removed 'Open in IDE' command from $KEYMAP"
else
    echo "Nothing to remove (marker not found in $KEYMAP)"
fi
