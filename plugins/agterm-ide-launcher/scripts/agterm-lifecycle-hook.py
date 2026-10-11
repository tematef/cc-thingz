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
import tempfile
import time

PROMPT_PATTERNS = [
    "run this command?",
    "requesting permission for",
    "allow command?",
    "press enter to confirm",
    "enter to submit answer",
    "enter to submit all",
    "1. yes, run command",
    "> 1. yes",
    "yes, and always allow",
    "proceed with plan?",
    "do you want to proceed?",
]


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


def run_agtermctl(args: list[str], sock: str | None = None) -> None:
    ctl = find_agtermctl()
    active_sock = sock or os.environ.get("AGTERM_SOCKET")
    cmd = [ctl] + args
    if active_sock:
        cmd += ["--socket", active_sock]
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


def read_visible_screen(
    sid: str,
    pane_id: str | None = None,
    sock: str | None = None,
) -> str | None:
    ctl = find_agtermctl()
    active_sock = sock or os.environ.get("AGTERM_SOCKET")
    cmd = [ctl, "session", "text", "--target", sid]
    if pane_id:
        cmd += ["--pane-id", pane_id]
    if active_sock:
        cmd += ["--socket", active_sock]
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.decode("utf-8", errors="replace")
    except Exception:
        pass
    return None


def get_watch_token_file(sid: str, pane_id: str | None = None) -> str:
    key_raw = f"{sid}-{pane_id or 'default'}"
    safe_key = "".join(c if c.isalnum() or c in "._-" else "_" for c in key_raw)
    uid = os.getuid() if hasattr(os, "getuid") else 0
    return os.path.join(tempfile.gettempdir(), f"agterm-agy-watch-{uid}-{safe_key}.token")


def stop_watcher(sid: str, pane_id: str | None = None) -> None:
    token_file = get_watch_token_file(sid, pane_id)
    try:
        if os.path.isfile(token_file):
            os.remove(token_file)
    except Exception:
        pass


def start_watcher(
    sid: str,
    pane_id: str | None = None,
    sock: str | None = None,
) -> None:
    token_file = get_watch_token_file(sid, pane_id)
    token = f"{os.getpid()}-{time.time()}"
    try:
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(token)
    except Exception:
        return

    cmd = [
        sys.executable,
        os.path.abspath(__file__),
        "__watch",
        token,
        token_file,
        sid,
        pane_id or "",
        sock or "",
    ]
    try:
        subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )
    except Exception:
        pass


def run_watcher(
    token: str,
    token_file: str,
    sid: str,
    pane_id: str | None,
    sock: str | None,
) -> None:
    config = load_config()
    target_args: list[str] = ["--target", sid]
    if pane_id:
        target_args += ["--pane-id", pane_id]

    max_checks = 21600  # 3 hours at 0.5s interval
    interval = 0.5
    checks = 0
    prompt_was_visible = False

    while checks < max_checks:
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                current_token = f.read().strip()
            if current_token != token:
                break
        except Exception:
            break

        screen = read_visible_screen(sid, pane_id, sock)
        if screen is not None:
            lines = screen.strip().splitlines()
            footer = "\n".join(lines[-15:]).lower()
            is_prompt = any(p in footer for p in PROMPT_PATTERNS)

            if is_prompt:
                if not prompt_was_visible:
                    # Double-check token before notifying to prevent race on stop
                    try:
                        with open(token_file, "r", encoding="utf-8") as f:
                            if f.read().strip() != token:
                                break
                    except Exception:
                        break

                    sound = resolve_sound("input", config, "Sosumi")
                    cmd = ["session", "status", "blocked"]
                    if sound:
                        cmd += ["--sound", sound]
                    cmd += ["--blink"] + target_args
                    run_agtermctl(cmd, sock=sock)
                    run_agtermctl(["notify", "Agent is waiting for your input", "--target", sid], sock=sock)
                    prompt_was_visible = True
            else:
                if prompt_was_visible:
                    # Prompt cleared (user answered or skipped)
                    try:
                        with open(token_file, "r", encoding="utf-8") as f:
                            if f.read().strip() != token:
                                break
                    except Exception:
                        break

                    run_agtermctl(["session", "status", "active", "--blink"] + target_args, sock=sock)
                    prompt_was_visible = False

        checks += 1
        time.sleep(interval)


def handle_event(mode: str, payload: dict) -> dict:
    sid = os.environ.get("AGTERM_SESSION_ID")
    pane_id = os.environ.get("AGTERM_PANE_ID")
    sock = os.environ.get("AGTERM_SOCKET")

    target_args: list[str] = []
    if sid:
        target_args += ["--target", sid]
    if pane_id:
        target_args += ["--pane-id", pane_id]

    if sid:
        config = load_config()

        if mode == "pre_invocation":
            stop_watcher(sid, pane_id)
            run_agtermctl(["session", "status", "active", "--blink"] + target_args, sock=sock)
            start_watcher(sid, pane_id, sock)

        elif mode == "ask_question":
            sound = resolve_sound("input", config, "Sosumi")
            cmd = ["session", "status", "blocked"]
            if sound:
                cmd += ["--sound", sound]
            cmd += ["--blink"] + target_args
            run_agtermctl(cmd, sock=sock)
            run_agtermctl(["notify", "Agent is waiting for your input"] + (["--target", sid] if sid else []), sock=sock)

        elif mode == "stop":
            err = bool(payload.get("error") or (payload.get("terminationReason") == "error"))
            if not err and payload.get("fullyIdle") is False:
                # Background tasks or subagents are still running; the session is still working.
                return {"decision": "allow"}

            stop_watcher(sid, pane_id)
            if err:
                sound = resolve_sound("error", config, "Sosumi")
                cmd = ["session", "status", "blocked"]
                if sound:
                    cmd += ["--sound", sound]
                cmd += ["--blink", "--auto-reset"] + target_args
                run_agtermctl(cmd, sock=sock)
                run_agtermctl(["notify", "Task stopped with error"] + (["--target", sid] if sid else []), sock=sock)
            else:
                sound = resolve_sound("completed", config, "Hero")
                cmd = ["session", "status", "completed"]
                if sound:
                    cmd += ["--sound", sound]
                cmd += ["--auto-reset"] + target_args
                run_agtermctl(cmd, sock=sock)
                run_agtermctl(["notify", "Task completed"] + (["--target", sid] if sid else []), sock=sock)

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

    # Test token file path and lifecycle
    tok_file = get_watch_token_file("test-session-123", "pane-left")
    assert "test-session-123" in tok_file
    assert "pane-left" in tok_file

    stop_watcher("test-session-123", "pane-left")
    assert not os.path.isfile(tok_file)

    # Test prompt pattern detection
    sample_permission_screen = (
        "Requesting permission for:\n"
        "  cat << 'EOF' > /tmp/extract_assets.swift\n"
        "Run this command?\n"
        "> 1. Yes, run command\n"
        "  2. No\n"
    )
    lines = sample_permission_screen.strip().splitlines()
    footer = "\n".join(lines[-15:]).lower()
    assert any(p in footer for p in PROMPT_PATTERNS)

    # Test event return schemas
    assert handle_event("pre_invocation", {}) == {"injectSteps": []}
    assert handle_event("ask_question", {}) == {"decision": "allow"}
    assert handle_event("stop", {}) == {"decision": "allow"}
    assert handle_event("stop", {"fullyIdle": False}) == {"decision": "allow"}
    assert handle_event("unknown", {}) == {}

    print("PASS: all agterm-lifecycle-hook tests passed")
    return 0


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sys.exit(run_tests())

    if len(sys.argv) > 1 and sys.argv[1] == "__watch":
        token = sys.argv[2] if len(sys.argv) > 2 else ""
        token_file = sys.argv[3] if len(sys.argv) > 3 else ""
        sid = sys.argv[4] if len(sys.argv) > 4 else ""
        pane_id = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else None
        sock = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] else None
        if token and token_file and sid:
            run_watcher(token, token_file, sid, pane_id, sock)
        sys.exit(0)

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
