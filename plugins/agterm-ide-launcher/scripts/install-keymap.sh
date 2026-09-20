#!/bin/bash
# install-keymap.sh — Append the "Open in IDE" command to agterm's keymap.conf and reload.
#
# Idempotent: removes any previous entry (identified by MARKER) before appending.
# Reads the shortcut chord from the user config file; defaults to ctrl+shift+e.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONF="$HOME/.gemini/config/plugins_data/cc-thingz/agterm-ide-launcher.conf"
KEYMAP="$HOME/.config/agterm/keymap.conf"
MARKER="# cc-thingz:agterm-ide-launcher"

# ── read shortcut from config or default ──────────────────────────────────────
SHORTCUT="ctrl+shift+e"
# shellcheck disable=SC1090
[ -f "$CONF" ] && . "$CONF"

# ── ensure keymap file exists ─────────────────────────────────────────────────
mkdir -p "$(dirname "$KEYMAP")"
[ -f "$KEYMAP" ] || touch "$KEYMAP"

# ── remove previous entry (idempotent) ────────────────────────────────────────
if grep -q "$MARKER" "$KEYMAP"; then
    grep -v "$MARKER" "$KEYMAP" > "${KEYMAP}.tmp" && mv "${KEYMAP}.tmp" "$KEYMAP"
fi

# ── append the command line ───────────────────────────────────────────────────
printf '\ncommand "Open in IDE"  %s  bash "%s/open-in-ide.sh"  %s\n' \
    "$SHORTCUT" "$SCRIPT_DIR" "$MARKER" >> "$KEYMAP"

# ── reload keymap ─────────────────────────────────────────────────────────────
agtermctl keymap reload 2>/dev/null || true

echo "✓ Registered 'Open in IDE' on ${SHORTCUT} in $KEYMAP"
echo "  Run 'agtermctl keymap list' to verify."
