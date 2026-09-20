---
name: agterm-ide
description: >-
  Install, configure, or uninstall the agterm "Open in Antigravity IDE"
  keyboard shortcut. Activates on "open in ide", "agterm ide", "ide shortcut",
  "install ide shortcut", "remove ide shortcut", "configure ide shortcut".
---

# agterm → Open in Antigravity IDE

A keyboard shortcut for agterm that pops up a native Yes/No picker and opens the
current session's working directory in Antigravity IDE.

## Install

Register the keymap binding in agterm:

```
run_command: bash plugins/agterm-ide-launcher/scripts/install-keymap.sh
```

This appends a `command` line to `~/.config/agterm/keymap.conf` and reloads the
keymap. The install is idempotent — running it again updates the entry in place.

## Configure

Edit `~/.gemini/config/plugins_data/cc-thingz/agterm-ide-launcher.conf`:

```bash
# Keyboard shortcut chord (agterm/kitty syntax)
SHORTCUT="ctrl+shift+e"

# Path to the Antigravity IDE binary
IDE_BIN="antigravity-ide"

# Picker prompt text
PICKER_PROMPT="Open in Antigravity IDE?"
```

After changing `SHORTCUT`, re-run `install-keymap.sh` to update the keymap.
Changes to `IDE_BIN` and `PICKER_PROMPT` take effect immediately (read at
invocation time).

### Shortcut syntax

Uses agterm's kitty-flavored chord syntax. Modifiers: `ctrl`, `cmd`, `opt`,
`shift`. Examples: `ctrl+shift+e`, `cmd+opt+i`, `ctrl+a>e` (leader sequence).

### IDE binary resolution

The launcher tries these locations in order:

1. The value of `IDE_BIN` (on `$PATH` or as an absolute path)
2. `~/.antigravity-ide/antigravity-ide/bin/antigravity-ide`
3. `/Applications/Antigravity IDE.app/Contents/Resources/bin/antigravity-ide`

## Uninstall

Remove the keymap binding:

```
run_command: bash plugins/agterm-ide-launcher/scripts/uninstall-keymap.sh
```

## How it works

1. User presses the configured shortcut in agterm
2. agterm runs `open-in-ide.sh` (fire-and-forget, no TTY)
3. The script calls `agtermctl pick open` with "Yes" / "No" choices
4. A native fuzzy picker popup appears in the agterm window
5. If "Yes" is selected, the IDE is launched with the session's working directory
6. If "No" or Escape, nothing happens

## Troubleshooting

- **Picker doesn't appear**: Ensure `agtermctl` is on `$PATH` and agterm is
  running. Check `agtermctl keymap list` for the binding.
- **IDE doesn't open**: Check that the IDE binary path is correct. The script
  posts an `agtermctl notify` error if the binary can't be found.
- **Shortcut conflict**: Check existing bindings with `agtermctl keymap list`
  and choose a different chord in the config file.
