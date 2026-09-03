#!/usr/bin/env python3
"""plan-review-hook.py - Stop hook for AGY/Jetski plan review.

intercepts the agent before it stops and opens the plan for user review. uses revdiff if
installed (syntax-highlighted TUI with line annotations), falls back to
plan-annotate.py ($EDITOR with unified diff) if not.

hook receives JSON on stdin with context (including artifactDirectoryPath).
returns Stop hook JSON response:
  - "allow"  → no changes/annotations, agent stops normally
  - "continue" → feedback found, sent as reason, forces agent to re-enter loop

requirements:
  - revdiff (preferred) or $EDITOR (fallback)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def read_context_from_stdin() -> dict:
    """read context from hook event JSON on stdin."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def make_response(decision: str, reason: str = "") -> None:
    """output Stop hook response and exit with appropriate code."""
    resp = {"decision": decision}
    if reason:
        resp["reason"] = reason
    print(json.dumps(resp, indent=2))
    sys.exit(0)


def try_revdiff(plan_content: str, plugin_root: str) -> str | None:
    """try reviewing plan with revdiff. returns annotations or None if revdiff unavailable."""
    if not shutil.which("revdiff"):
        return None

    launcher = Path(plugin_root) / "scripts" / "launch-plan-review.sh"
    if not launcher.exists():
        return None

    # write plan to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", prefix="plan-review-", delete=False
    ) as tmp:
        tmp.write(plan_content)
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [str(launcher), str(tmp_path)],
            capture_output=True, text=True, timeout=345600,
            env={**os.environ},
        )
        if result.returncode != 0:
            return None  # launcher failed; fall through to plan-annotate.py
        annotations = result.stdout.strip()
        if not annotations:
            return ""
        return (
            "User reviewed the plan in revdiff and added annotations. "
            "Each annotation references a specific line and contains the user's feedback.\n\n"
            f"{annotations}\n\n"
            "Adjust the plan to address each annotation."
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def main() -> None:
    context = read_context_from_stdin()
    artifact_dir = context.get("artifactDirectoryPath")
    if not artifact_dir:
        make_response("allow", "no artifactDirectoryPath in hook context")
        return

    plan_path = Path(artifact_dir) / "implementation_plan.md"
    if not plan_path.exists():
        # no plan created yet, let it stop normally
        make_response("allow", "implementation_plan.md not found")
        return
        
    try:
        plan_content = plan_path.read_text()
    except Exception as e:
        make_response("allow", f"could not read plan: {e}")
        return

    if os.environ.get("PLANNING_DISABLE_REVDIFF"):
        make_response("allow", "plan review disabled via PLANNING_DISABLE_REVDIFF")
        return

    import hashlib
    plan_hash = hashlib.sha256(plan_content.encode("utf-8")).hexdigest()
    hash_file = Path(artifact_dir) / ".plan_reviewed.hash"

    if hash_file.exists() and hash_file.read_text().strip() == plan_hash:
        make_response("allow", "plan already reviewed and unchanged")
        return

    # In AGY, the script runs with CWD set to the plugin directory (where hooks.json is)
    plugin_root = Path(__file__).resolve().parents[1]

    # try revdiff first
    result = try_revdiff(plan_content, str(plugin_root))
    if result is not None:
        if not result:
            hash_file.write_text(plan_hash)
            make_response("allow", "plan reviewed, no annotations")
        else:
            make_response("continue", result)
        return

    # fall back to plan-annotate.py
    annotate_script = Path(plugin_root) / "scripts" / "plan-annotate.py"
    if not annotate_script.exists():
        make_response("allow", "no review tool available (revdiff not installed, plan-annotate.py not found)")
        return

    # we simulate the old Claude payload format for the fallback script since we aren't changing it deeply here
    stdin_data = json.dumps({"tool_input": {"plan": plan_content}})
    fallback = subprocess.run(
        [sys.executable, str(annotate_script)],
        input=stdin_data, capture_output=True, text=True, timeout=345600,
        env={**os.environ},
    )

    # plan-annotate.py outputs the Claude hook JSON format; let's parse it and translate to AGY
    output = fallback.stdout.strip()
    if output:
        try:
            fallback_json = json.loads(output)
            decision = fallback_json.get("hookSpecificOutput", {}).get("permissionDecision")
            reason = fallback_json.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
            if decision == "deny":
                make_response("continue", reason)
            else:
                hash_file.write_text(plan_hash)
                make_response("allow", reason)
        except json.JSONDecodeError:
            make_response("allow", "fallback script returned invalid json")
    else:
        hash_file.write_text(plan_hash)
        make_response("allow", "plan reviewed, no changes")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\r\033[K", end="")
        sys.exit(130)
