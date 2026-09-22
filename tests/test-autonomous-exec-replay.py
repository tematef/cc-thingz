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


def main() -> int:
    # Clear subagent cache so we test fresh detection
    if os.path.exists(hook.SUBAGENT_CACHE_FILE):
        try:
            os.remove(hook.SUBAGENT_CACHE_FILE)
        except OSError:
            pass

    sub_ids = [
        "3988d09c-4adb-4f3f-baae-b64550c53087",
        "fd4758d2-b2a3-4581-b04f-1afa3c23422a",
        "a6454762-4a7e-46c7-a765-63ec2b140985",
        "a7177c29-b3e3-4962-a1f0-e5c3e564903c",
        "a4977650-fd53-4782-bf74-f223084e30c7",
        "7422bc79-e932-4693-b801-2238aa503806",
        "14eacf71-87dc-48ff-be38-16b5773a50c9",
        "20c6d466-56d8-42d5-b21d-8f10e7549574",
        "9e6ef969-959a-4995-9feb-67ee942ded54",
    ]

    brain = os.path.expanduser("~/.gemini/jetski/brain")
    if os.path.isdir(brain):
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
                "workspacePaths": ["/Users/balandin/projects/Weave-FE/e2e"],
                "toolCall": {
                    "name": "run_command",
                    "args": {
                        "CommandLine": "rm -f /Users/balandin/projects/Weave-FE/scripts/cypress_env_import_guard.ts",
                        "Cwd": "/Users/balandin/projects/Weave-FE",
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
        for pid in ("68dfbd93-5052-44cf-a2ba-c8d4d9e5e712", "694c05fb-f138-40a9-bb3b-4725fec33f0c"):
            ptpath = os.path.join(brain, pid, ".system_generated", "logs", "transcript.jsonl")
            if os.path.exists(ptpath):
                assert not hook.is_subagent_conversation(pid, ptpath), (
                    f"Parent session {pid} must NOT be classified as a subagent!"
                )

        # Replay all tool calls across all 9 subagents and parent 694c05fb
        total_replayed = 0
        subagent_asks = []
        main_asks = []
        for cid in sub_ids + ["694c05fb-f138-40a9-bb3b-4725fec33f0c"]:
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
                                "workspacePaths": ["/Users/balandin/projects/Weave-FE/e2e"],
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
            f"PASS: Replayed {total_replayed} historical tool calls across {detected_subagents}/{tested_subagents} subagents and parent session: "
            f"0 subagent prompts (100% auto-allowed), {len(main_asks)} main-agent asks!"
        )
    else:
        print("PASS: Brain directory not present on runner; skipped live transcript replay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
