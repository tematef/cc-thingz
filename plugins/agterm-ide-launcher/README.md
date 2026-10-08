# agterm-ide-launcher

Terminal integration for **agterm**:
1. **IDE Launcher**: A keyboard shortcut (`ctrl+shift+e`) that opens the current terminal session's project directory in **Antigravity IDE** via a native Yes/No confirmation popup.
2. **Agent Status & Alerts**: Lifecycle hooks that update agterm session status indicators (active, blocked, completed), send desktop notifications, and optionally play audio alert chimes when an agent needs user input or completes a task.

## Prerequisites

- **agterm** — the Antigravity terminal application
- **agtermctl** — agterm's CLI control tool (bundled with agterm on `$PATH` or in standard locations)
- **Antigravity IDE** — installed and on `$PATH`, or at one of the standard application locations

## Features

### 1. IDE Launcher Shortcut

- Press `ctrl+shift+e` inside agterm.
- Native popup prompt appears (`1. Yes / 2. No`).
- Selecting "Yes" opens the project directory of the active session in Antigravity IDE.

```bash
# Install the keymap binding in ~/.config/agterm/keymap.conf
bash plugins/agterm-ide-launcher/scripts/install-keymap.sh
```

### 2. Session Status Indicators & Notifications

Lifecycle hooks automatically track agent execution when running inside agterm (`$AGTERM_SESSION_ID` is set):
- **Active execution (`PreInvocation`)**: Sets session status to `active` with a pulsing tab indicator (`--blink`).
- **Waiting for user input (`PreToolUse: ask_question`)**: Sets session status to `blocked` (blinking), sends a desktop notification (`"Agent is waiting for your input"`), and optionally plays an alert sound.
- **Task completed (`Stop`)**: Sets status to `completed` (with `--auto-reset` once the tab is focused), sends a desktop notification (`"Task completed"`), and optionally plays a completion chime. If the task ends with an error, status is marked `blocked` with an error chime and notification.

Audio alerts are **optional and disabled by default** so agent runs stay quiet unless explicitly configured.

## Configuration

Create or edit `~/.gemini/config/plugins_data/cc-thingz/agterm-ide-launcher.conf` (or `~/.config/agterm/agterm-ide-launcher.conf`):

```bash
# ── Launcher Shortcut ──────────────────────────────────────────────────────────
# Keyboard shortcut chord (agterm/kitty syntax)
SHORTCUT="ctrl+shift+e"

# Path to the Antigravity IDE binary (name on $PATH or absolute path)
IDE_BIN="antigravity-ide"

# Prompt text shown in the picker popup
PICKER_PROMPT="Open in Antigravity IDE?"

# ── Alert Sounds ───────────────────────────────────────────────────────────────
# Enable audio alerts on status changes (default: false)
# Set to "true" to enable sounds, or "false" to keep alerts silent.
# Can also be set directly to a system sound name (e.g. ALERT_SOUND="Ping").
ALERT_SOUND="false"

# Specific sound names (used when ALERT_SOUND="true")
# Available system sounds on macOS:
#   Basso, Blow, Bottle, Frog, Funk, Glass, Hero, Morse,
#   Ping, Pop, Purr, Sosumi, Submarine, Tink, default
SOUND_INPUT="Sosumi"      # when waiting for input (ask_question)
SOUND_COMPLETED="Hero"    # when task completes successfully
SOUND_ERROR="Sosumi"      # when task stops with error
```

### Environment Overrides

Sound settings can also be toggled via environment variables:
- `AGTERM_ALERT_SOUND=true` (or `false`)
- `AGTERM_SOUND_INPUT=<name>`
- `AGTERM_SOUND_COMPLETED=<name>`
- `AGTERM_SOUND_ERROR=<name>`

After changing `SHORTCUT`, re-run `install-keymap.sh` to update the agterm keymap. All other settings take effect immediately on next invocation without reinstalling.

## Uninstall

```bash
# Remove keymap binding from ~/.config/agterm/keymap.conf
bash plugins/agterm-ide-launcher/scripts/uninstall-keymap.sh
```

To disable the lifecycle hooks, disable the plugin or remove the plugin symlink.

## Files

| File | Purpose |
|------|---------|
| `plugin.json` | AGY plugin manifest (`cc-thingz-agterm-ide-launcher`) |
| `hooks.json` | Lifecycle hooks registration (`agterm-agent-status`) |
| `scripts/agterm-lifecycle-hook.py` | Session status indicators, desktop notifications, and optional sound alerts |
| `scripts/open-in-ide.sh` | Main launcher (called by agterm keymap command) |
| `scripts/install-keymap.sh` | Registers the shortcut in `~/.config/agterm/keymap.conf` |
| `scripts/uninstall-keymap.sh` | Removes the shortcut from `keymap.conf` |
