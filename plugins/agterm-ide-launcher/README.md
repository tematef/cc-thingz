# agterm-ide-launcher

An agterm keyboard shortcut that opens the current terminal session's project directory in **Antigravity IDE** via a native Yes/No confirmation popup.

## Prerequisites

- **agterm** — the Antigravity terminal application
- **agtermctl** — agterm's CLI control tool (bundled with agterm)
- **Antigravity IDE** — installed and on `$PATH`, or at one of the standard locations

## Quick Start

```bash
# Install the keymap binding
bash plugins/agterm-ide-launcher/scripts/install-keymap.sh

# Press ctrl+shift+e in agterm → pick Yes → IDE opens
```

## Configuration

Create or edit `~/.gemini/config/plugins_data/cc-thingz/agterm-ide-launcher.conf`:

```bash
# Keyboard shortcut chord (agterm/kitty syntax)
SHORTCUT="ctrl+shift+e"

# Path to the Antigravity IDE binary (name on $PATH or absolute path)
IDE_BIN="antigravity-ide"

# Prompt text shown in the picker popup
PICKER_PROMPT="Open in Antigravity IDE?"
```

After changing `SHORTCUT`, re-run `install-keymap.sh` to update the agterm keymap.
`IDE_BIN` and `PICKER_PROMPT` take effect immediately on next invocation.

## How It Works

1. User presses the configured shortcut (default `ctrl+shift+e`)
2. agterm fires `open-in-ide.sh` via its keymap `command` directive
3. The script opens a native fuzzy picker with `agtermctl pick open`
4. If "Yes" is selected, the IDE launches with the session's working directory
5. If "No" or Escape, nothing happens

## Uninstall

```bash
bash plugins/agterm-ide-launcher/scripts/uninstall-keymap.sh
```

## Files

| File | Purpose |
|------|---------|
| `plugin.json` | AGY plugin manifest |
| `scripts/open-in-ide.sh` | Main launcher (called by agterm keymap command) |
| `scripts/install-keymap.sh` | Registers the shortcut in `~/.config/agterm/keymap.conf` |
| `scripts/uninstall-keymap.sh` | Removes the shortcut from `keymap.conf` |

