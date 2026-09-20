#!/bin/bash
# open-in-ide.sh — agterm custom command: prompt, then open session dir in Antigravity IDE.
#
# Called by agterm's keymap engine with $AGT_SESSION_PWD, $AGT_SOCKET set.
# Shows a native Yes/No picker; if "Yes", launches the IDE in the session's directory.
#
# Configuration is read from:
#   ~/.gemini/config/plugins_data/cc-thingz/agterm-ide-launcher.conf
#
# Config keys (shell key=value):
#   IDE_BIN         — path or name of the Antigravity IDE binary (default: antigravity-ide)
#   PICKER_PROMPT   — prompt text for the picker popup (default: "Open in Antigravity IDE?")

LOG="/tmp/agterm-ide-launcher.log"
exec >> "$LOG" 2>&1
echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="

# Ensure standard PATH for GUI app subprocesses
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$HOME/.local/bin:$HOME/bin:$HOME/.antigravity-ide/antigravity-ide/bin:$PATH"

CONF="$HOME/.gemini/config/plugins_data/cc-thingz/agterm-ide-launcher.conf"

# ── defaults ──────────────────────────────────────────────────────────────────
IDE_BIN="antigravity-ide"
PICKER_PROMPT="Open in Antigravity IDE?"

# ── source user config (if present) ──────────────────────────────────────────
# shellcheck disable=SC1090
[ -f "$CONF" ] && . "$CONF"

echo "CONF=$CONF"
echo "IDE_BIN=$IDE_BIN"

# ── resolve project directory ─────────────────────────────────────────────────
PROJECT_DIR="${AGT_SESSION_PWD:-${PWD:-$HOME}}"
echo "PROJECT_DIR=$PROJECT_DIR"

# ── resolve agtermctl ─────────────────────────────────────────────────────────
AGTERMCTL="${AGTERMCTL:-}"
if [ -z "$AGTERMCTL" ] || ! command -v "$AGTERMCTL" >/dev/null 2>&1; then
    for candidate in \
        "$(command -v agtermctl 2>/dev/null || true)" \
        "/opt/homebrew/bin/agtermctl" \
        "/usr/local/bin/agtermctl" \
        "/Applications/agterm.app/Contents/MacOS/agtermctl" \
        "${GHOSTTY_BIN_DIR:-}/agtermctl"; do
        if [ -n "$candidate" ] && [ -x "$candidate" ]; then
            AGTERMCTL="$candidate"
            break
        fi
    done
fi

echo "AGTERMCTL=$AGTERMCTL"

if [ -z "$AGTERMCTL" ] || [ ! -x "$AGTERMCTL" ]; then
    echo "error: agtermctl not found" >&2
    exit 1
fi

# ── build agtermctl base args ─────────────────────────────────────────────────
AGTERM_ARGS=()
SOCKET="${AGT_SOCKET:-${AGTERM_SOCKET:-}}"
if [ -n "$SOCKET" ]; then
    AGTERM_ARGS+=(--socket "$SOCKET")
fi

echo "SOCKET=$SOCKET"

# ── show native Yes/No picker ─────────────────────────────────────────────────
# Note: agterm's native picker sorts choices alphabetically. Prefixing with numbers
# ensures "1. Yes" appears first and is focused/selected by default on Enter.
RAW_CHOICE=$(printf "1. Yes\n2. No\n" \
    | "$AGTERMCTL" pick open --prompt "$PICKER_PROMPT" ${AGTERM_ARGS[@]+"${AGTERM_ARGS[@]}"} 2>/dev/null) || true

# Strip any carriage returns or newlines
CHOICE=$(echo "$RAW_CHOICE" | tr -d '\r\n')
echo "RAW_CHOICE='$RAW_CHOICE' -> CHOICE='$CHOICE'"

# agtermctl pick open returns JSON like:
# {"label":"1. Yes","index":0,"result":"picked","id":"1. Yes"} or {"result":"cancelled"}
IS_YES=0
if echo "$CHOICE" | grep -qE '"(label|id)":"(1\.\s*)?Yes'; then
    IS_YES=1
fi

if [ "$IS_YES" -eq 1 ]; then
    echo "User confirmed Yes. Launching IDE..."
    LAUNCHED=0

    # Method 1: On macOS, use open -a if Antigravity IDE.app is installed and IDE_BIN is default
    if [ "$IDE_BIN" = "antigravity-ide" ] && [ -d "/Applications/Antigravity IDE.app" ]; then
        echo "Launching via open -a 'Antigravity IDE' '$PROJECT_DIR'..."
        if open -a "Antigravity IDE" "$PROJECT_DIR"; then
            LAUNCHED=1
        fi
    fi

    # Method 2: Use resolved IDE binary
    if [ "$LAUNCHED" -eq 0 ]; then
        IDE_CMD="$IDE_BIN"
        if ! command -v "$IDE_CMD" >/dev/null 2>&1 && [ ! -x "$IDE_CMD" ]; then
            for candidate in \
                "$HOME/.antigravity-ide/antigravity-ide/bin/antigravity-ide" \
                "/Applications/Antigravity IDE.app/Contents/Resources/bin/antigravity-ide" \
                "/Applications/Antigravity IDE.app/Contents/MacOS/Electron"; do
                if [ -x "$candidate" ]; then
                    IDE_CMD="$candidate"
                    break
                fi
            done
        fi

        echo "IDE_CMD=$IDE_CMD"

        if command -v "$IDE_CMD" >/dev/null 2>&1 || [ -x "$IDE_CMD" ]; then
            echo "Launching via '$IDE_CMD' '$PROJECT_DIR'..."
            "$IDE_CMD" "$PROJECT_DIR" </dev/null >/dev/null 2>&1 &
            disown
            LAUNCHED=1
        fi
    fi

    if [ "$LAUNCHED" -eq 0 ]; then
        echo "Failed to find or launch IDE!" >&2
        "$AGTERMCTL" notify "IDE binary not found: $IDE_BIN" \
            --title "Open in IDE" ${AGTERM_ARGS[@]+"${AGTERM_ARGS[@]}"} 2>/dev/null || true
        exit 1
    fi

    echo "Successfully launched IDE."
    exit 0
else
    echo "Cancelled or chose No: '$CHOICE'"
    exit 0
fi
