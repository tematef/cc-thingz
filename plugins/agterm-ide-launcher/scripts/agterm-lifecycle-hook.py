#!/usr/bin/env python3
"""agterm-lifecycle-hook.py - Updates agterm agent session status and notifications.

Fires on AGY agent lifecycle events:
  - PreInvocation: sets session status to 'active' (pulsing tab / indicator)
  - PreToolUse (ask_question): sets status to 'blocked' (with blink and optional sound),
    and sends desktop notification that agent awaits user input.
  - Stop: sets status to 'completed' (or 'blocked' on error) with auto-reset and optional sound,
    and sends desktop notification.

Configuration is loaded from:
  ~/.config/agterm/agterm-ide-launcher.conf
  ~/.gemini/config/plugins_data/cc-thingz/agterm-ide-launcher.conf

Keys:
  ALERT_SOUND         - "true" / "false" (default: false). Enable or disable audio alerts.
  SOUND_INPUT         - Sound name when waiting for input (default: "Sosumi").
  SOUND_COMPLETED     - Sound name on successful completion (default: "Hero").
  SOUND_ERROR         - Sound name on task failure (default: "Sosumi").
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys


def find_agtermctl() -> str:
    candidate = shutil.which("agtermctl")
    if candidate:
        return candidate
    for path in (
        "/opt/homebrew/bin/agtermctl",
        "/usr/local/bin/agtermctl",
        "/Applications/agterm.app/Contents/MacOS/agtermctl",
        os.path.expanduser("~/.local/bin/agtermctl"),
    ):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return "agtermctl"


def load_config() -> dict[str, str]:
    conf_paths = [
        os.path.expanduser("~/.config/agterm/agterm-ide-launcher.conf"),
        os.path.expanduser("~/.gemini/config/plugins_data/cc-thingz/agterm-ide-launcher.conf"),
    ]
    config: dict[str, str] = {}
    for path in conf_paths:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if (v.startswith('"') and v.endswith('"')) or (
                            v.startswith("'") and v.endswith("'")
                        ):
                            v = v[1:-1]
                        config[k] = v
        except Exception:
            pass
    return config


def resolve_sound(
    event_type: str,
    config: dict[str, str],
    default_name: str,
) -> str | None:
    """Returns the sound name to play for an event type, or None if sound is disabled."""
    env_sound = os.environ.get("AGTERM_ALERT_SOUND") or os.environ.get("AGTERM_SOUND")
    conf_sound = config.get("ALERT_SOUND") or config.get("ENABLE_SOUND") or config.get("SOUND")
    sound_setting = (env_sound if env_sound is not None else (conf_sound or "")).strip()

    truthy = {"1", "true", "yes", "on", "enable", "enabled"}
    falsy = {"0", "false", "no", "off", "disable", "disabled", "none", ""}

    sound_enabled = False
    custom_sound = None

    if sound_setting:
        val_lower = sound_setting.lower()
        if val_lower in truthy:
            sound_enabled = True
        elif val_lower in falsy:
            sound_enabled = False
        else:
            # Explicit sound name provided in general setting (e.g. ALERT_SOUND="Hero")
            sound_enabled = True
            custom_sound = sound_setting

    if not sound_enabled:
        return None

    if event_type == "input":
        return (
            os.environ.get("AGTERM_SOUND_INPUT")
            or config.get("SOUND_INPUT")
            or custom_sound
            or default_name
        )
    elif event_type == "completed":
        return (
            os.environ.get("AGTERM_SOUND_COMPLETED")
            or config.get("SOUND_COMPLETED")
            or custom_sound
            or default_name
        )
    elif event_type == "error":
        return (
            os.environ.get("AGTERM_SOUND_ERROR")
            or config.get("SOUND_ERROR")
            or custom_sound
            or default_name
        )
    return custom_sound or default_name


def run_agtermctl(args: list[str]) -> None:
    ctl = find_agtermctl()
    sock = os.environ.get("AGTERM_SOCKET")
    cmd = [ctl] + args
    if sock:
        cmd += ["--socket", sock]
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
    except Exception:
        pass


def handle_event(mode: str, payload: dict) -> dict:
    sid = os.environ.get("AGTERM_SESSION_ID")
    pane_id = os.environ.get("AGTERM_PANE_ID")

    target_args: list[str] = []
    if sid:
        target_args += ["--target", sid]
    if pane_id:
        target_args += ["--pane-id", pane_id]

    if sid:
        config = load_config()

        if mode == "pre_invocation":
            run_agtermctl(["session", "status", "active", "--blink"] + target_args)

        elif mode == "ask_question":
            sound = resolve_sound("input", config, "Sosumi")
            cmd = ["session", "status", "blocked"]
            if sound:
                cmd += ["--sound", sound]
            cmd += ["--blink"] + target_args
            run_agtermctl(cmd)
            run_agtermctl(["notify", "Agent is waiting for your input"] + (["--target", sid] if sid else []))

        elif mode == "stop":
            err = bool(payload.get("error") or (payload.get("terminationReason") == "error"))
            if err:
                sound = resolve_sound("error", config, "Sosumi")
                cmd = ["session", "status", "blocked"]
                if sound:
                    cmd += ["--sound", sound]
                cmd += ["--blink", "--auto-reset"] + target_args
                run_agtermctl(cmd)
                run_agtermctl(["notify", "Task stopped with error"] + (["--target", sid] if sid else []))
            else:
                sound = resolve_sound("completed", config, "Hero")
                cmd = ["session", "status", "completed"]
                if sound:
                    cmd += ["--sound", sound]
                cmd += ["--auto-reset"] + target_args
                run_agtermctl(cmd)
                run_agtermctl(["notify", "Task completed"] + (["--target", sid] if sid else []))

    if mode == "pre_invocation":
        return {"injectSteps": []}
    elif mode in ("stop", "ask_question"):
        return {"decision": "allow"}
    return {}


def run_tests() -> int:
    # Test sound resolution
    cfg_empty: dict[str, str] = {}
    assert resolve_sound("input", cfg_empty, "Sosumi") is None, "default should be sound disabled"

    cfg_enabled = {"ALERT_SOUND": "true"}
    assert resolve_sound("input", cfg_enabled, "Sosumi") == "Sosumi"
    assert resolve_sound("completed", cfg_enabled, "Hero") == "Hero"
    assert resolve_sound("error", cfg_enabled, "Sosumi") == "Sosumi"

    cfg_custom = {
        "ALERT_SOUND": "true",
        "SOUND_INPUT": "Pop",
        "SOUND_COMPLETED": "Glass",
        "SOUND_ERROR": "Basso",
    }
    assert resolve_sound("input", cfg_custom, "Sosumi") == "Pop"
    assert resolve_sound("completed", cfg_custom, "Hero") == "Glass"
    assert resolve_sound("error", cfg_custom, "Sosumi") == "Basso"

    cfg_named_default = {"ALERT_SOUND": "Ping"}
    assert resolve_sound("input", cfg_named_default, "Sosumi") == "Ping"

    cfg_disabled = {"ALERT_SOUND": "false", "SOUND_INPUT": "Pop"}
    assert resolve_sound("input", cfg_disabled, "Sosumi") is None

    # Test event return schemas
    assert handle_event("pre_invocation", {}) == {"injectSteps": []}
    assert handle_event("ask_question", {}) == {"decision": "allow"}
    assert handle_event("stop", {}) == {"decision": "allow"}
    assert handle_event("unknown", {}) == {}

    print("PASS: all agterm-lifecycle-hook tests passed")
    return 0


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sys.exit(run_tests())

    mode = sys.argv[1] if len(sys.argv) > 1 else "stop"

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    response = handle_event(mode, payload)
    print(json.dumps(response))


if __name__ == "__main__":
    main()
