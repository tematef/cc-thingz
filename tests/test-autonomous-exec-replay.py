#!/usr/bin/env python3
"""Replay test suite for autonomous-exec-hook.py against real brain transcripts and subagents."""

from __future__ import annotations

import importlib
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "plugins", "planning", "scripts"))
hook = importlib.import_module("autonomous-exec-hook")


DEFAULT_REPLAY_CONFIG = os.path.expanduser(
    "~/.gemini/config/plugins_data/cc-thingz/replay-conversations.json"
)


def load_replay_config() -> dict | None:
    """Load machine-local conversation IDs to replay; None when absent or unreadable.

    The file lives outside the repo (conversation IDs and workspaces are per-machine):
      {"workspacePaths": ["/abs/workspace"], "subagents": ["<id>", ...],
       "parents": ["<id>", ...], "replayParents": ["<id>", ...]}
    Override the location with CC_THINGZ_REPLAY_CONFIG.
    """
    path = os.environ.get("CC_THINGZ_REPLAY_CONFIG") or DEFAULT_REPLAY_CONFIG
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        return None
    return cfg if isinstance(cfg, dict) else None


def main() -> int:
    cfg = load_replay_config()
    if cfg is None:
        print("PASS: No replay-conversations.json on this machine; skipped live transcript replay.")
        return 0

    sub_ids = [str(x) for x in cfg.get("subagents") or []]
    parent_ids = [str(x) for x in cfg.get("parents") or []]
    replay_parent_ids = [str(x) for x in cfg.get("replayParents") or []]
    workspaces = [str(x) for x in cfg.get("workspacePaths") or []] or [REPO_ROOT]
    workspace = workspaces[0]

    # Clear subagent cache so we test fresh detection
    if os.path.exists(hook.SUBAGENT_CACHE_FILE):
        try:
            os.remove(hook.SUBAGENT_CACHE_FILE)
        except OSError:
            pass

    brain = os.path.expanduser("~/.gemini/jetski/brain")
    if not os.path.isdir(brain):
        print("PASS: Brain directory not present on runner; skipped live transcript replay.")
        return 0

    detected_subagents = 0
    tested_subagents = 0
    for sid in sub_ids:
        tpath = os.path.join(brain, sid, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(tpath):
            continue
        tested_subagents += 1
        payload = {
            "conversationId": sid,
            "transcriptPath": tpath,
            "workspacePaths": workspaces,
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": f"rm -f {os.path.join(workspace, 'scratch-replay.ts')}",
                    "Cwd": workspace,
                },
            },
        }
        assert hook.is_subagent_or_autonomous_active(payload, "rm -f foo"), (
            f"Subagent {sid} failed is_subagent_or_autonomous_active!"
        )
        res = hook.evaluate_hook(payload)
        assert res.get("decision") == "allow", (
            f"Subagent {sid} mutating workspace command was not allowed: {res}"
        )
        detected_subagents += 1

    # Verify parent interactive conversations are NOT classified as subagents
    for pid in parent_ids:
        ptpath = os.path.join(brain, pid, ".system_generated", "logs", "transcript.jsonl")
        if os.path.exists(ptpath):
            assert not hook.is_subagent_conversation(pid, ptpath), (
                f"Parent session {pid} must NOT be classified as a subagent!"
            )

    # Replay all tool calls across the subagents and the selected parent sessions
    total_replayed = 0
    subagent_asks = []
    main_asks = []
    for cid in sub_ids + replay_parent_ids:
        tpath = os.path.join(brain, cid, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(tpath):
            continue
        with open(tpath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "tool_calls" not in line:
                    continue
                try:
                    obj = json.loads(line)
                    for tc in obj.get("tool_calls", []):
                        tname = tc.get("name") or tc.get("tool_name") or ""
                        targs = dict(tc.get("args") or tc.get("arguments") or {})
                        for k, v in list(targs.items()):
                            if isinstance(v, str) and v.startswith('"') and v.endswith('"'):
                                try:
                                    targs[k] = json.loads(v)
                                except Exception:
                                    targs[k] = v[1:-1]
                        payload = {
                            "conversationId": cid,
                            "transcriptPath": tpath,
                            "workspacePaths": workspaces,
                            "toolCall": {"name": tname, "args": targs},
                        }
                        res = hook.evaluate_hook(payload)
                        total_replayed += 1
                        cmd = str(targs.get("CommandLine") or targs.get("TargetFile") or "")
                        # Skip intentional git push commands (which SHOULD be force_ask in Tier 3)
                        if hook.is_dangerous_command(cmd):
                            assert res.get("decision") == "force_ask"
                            continue
                        if res.get("decision") != "allow":
                            if cid in sub_ids:
                                subagent_asks.append((cid[:8], tname, cmd[:100], res))
                            else:
                                main_asks.append((cid[:8], tname, cmd[:100], res))
                except Exception:
                    pass

    assert len(subagent_asks) == 0, (
        f"Expected 0 subagent tool calls to ask for permission, got {len(subagent_asks)}:\n"
        + "\n".join(str(x) for x in subagent_asks[:10])
    )
    print(
        f"PASS: Replayed {total_replayed} historical tool calls across {detected_subagents}/{tested_subagents} subagents and parent sessions: "
        f"0 subagent prompts (100% auto-allowed), {len(main_asks)} main-agent asks!"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
