#!/usr/bin/env python3
"""PreInvocation hook for Jetski / Antigravity (AGY): send ralphex plans to docs/plans.

ralphex-planner (shipped with the external ralphex tool, not with cc-thingz)
always saves plans under `.ralphex/plans/`. cc-thingz keeps plans in the
project's `docs/plans/`, resolved by `resolve-project-dir.sh`, and ralphex
archives a finished plan into a `completed/` folder next to the plan file.

This hook turns the nearest existing `.ralphex/plans` into a relative symlink
to the resolved `docs/plans`. New ralphex plans then land in `docs/plans/`, and
ralphex archives them into `docs/plans/completed/`, with no change to ralphex,
its skills, or any project.

For every entry in the payload's `workspacePaths` (the payload has no cwd):
  1. skip unless the workspace is inside a git or hg repository;
  2. skip unless a `.ralphex/` directory exists between the workspace and the
     VCS root; `.ralphex/` is never created;
  3. resolve `<project>/docs/plans` with the shared `resolve-project-dir.sh`
     (the same project root /planning:make uses; no override is applied);
  4. take the nearest `.ralphex/` at or above that project, up to the VCS root;
  5. create the link only when `.ralphex/plans` is missing or an empty
     directory. An existing symlink (wherever it points) and a directory that
     already holds files are left untouched. A `.ralphex/` shared by several
     projects (a repo-root one above sub-projects with their own AGENTS.md)
     therefore stays linked to the first project that reached it.

The hook is silent: it always prints `{}` and exits 0. What it did or skipped
goes to stderr only. Run with `--test` for the embedded unit tests.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
RESOLVER = os.path.join(SCRIPT_DIR, "resolve-project-dir.sh")
PLANS_SUBDIR = "docs/plans"
SUBPROCESS_TIMEOUT = 3


def log(message: str) -> None:
    print(f"ralphex-plans-link: {message}", file=sys.stderr)


def workspace_paths(raw: str) -> list[str]:
    """Existing directories listed in the payload's workspacePaths, in order."""
    try:
        payload = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(payload, dict):
        return []
    paths = payload.get("workspacePaths")
    if not isinstance(paths, list):
        return []
    return [p for p in paths if isinstance(p, str) and p and os.path.isdir(p)]


def vcs_root(cwd: str) -> str | None:
    """Physical git or hg root containing cwd, or None outside any VCS."""
    for cmd in (["git", "rev-parse", "--show-toplevel"], ["hg", "root"]):
        try:
            out = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT
            )
        except (OSError, subprocess.SubprocessError):
            continue
        root = out.stdout.strip()
        if out.returncode == 0 and root:
            return os.path.realpath(root)
    return None


def resolve_plans_dir(cwd: str) -> str | None:
    """`<project>/docs/plans` for cwd, via the shared resolver; None on failure."""
    try:
        out = subprocess.run(
            ["bash", RESOLVER, PLANS_SUBDIR],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    path = out.stdout.strip()
    if out.returncode != 0 or not path.endswith("/" + PLANS_SUBDIR):
        return None
    return path


def nearest_ralphex(start: str, stop: str) -> str | None:
    """Nearest dir from start up to stop (inclusive) holding a .ralphex/ directory."""
    current = os.path.realpath(start)
    stop = os.path.realpath(stop)
    while True:
        if os.path.isdir(os.path.join(current, ".ralphex")):
            return current
        parent = os.path.dirname(current)
        if current == stop or parent == current:
            return None
        current = parent


def link_target(ralphex_root: str, plans_dir: str) -> str:
    """Relative symlink target for <ralphex_root>/.ralphex/plans -> plans_dir."""
    base = os.path.realpath(os.path.join(ralphex_root, ".ralphex"))
    return os.path.relpath(os.path.realpath(plans_dir), base)


def ensure_link(ralphex_root: str, plans_dir: str) -> str:
    """Create .ralphex/plans -> plans_dir when safe; return what happened."""
    link = os.path.join(ralphex_root, ".ralphex", "plans")
    if os.path.islink(link):
        return "skip: .ralphex/plans is already a symlink"
    if os.path.isdir(link):
        if os.listdir(link):
            return "skip: .ralphex/plans holds files, left untouched"
    elif os.path.lexists(link):
        return "skip: .ralphex/plans is not a directory"
    os.makedirs(plans_dir, exist_ok=True)
    target = link_target(ralphex_root, plans_dir)
    if os.path.isdir(link):
        os.rmdir(link)
    os.symlink(target, link)
    return f"linked .ralphex/plans -> {target}"


def process(raw: str) -> list[str]:
    """Apply the link rule to every workspace; return log lines."""
    actions: list[str] = []
    seen: set[str] = set()
    for workspace in workspace_paths(raw):
        try:
            stop = vcs_root(workspace)
            if not stop:
                continue
            # cheap pre-check: every candidate is an ancestor of the workspace
            if nearest_ralphex(workspace, stop) is None:
                continue
            plans_dir = resolve_plans_dir(workspace)
            if not plans_dir:
                continue
            project = plans_dir[: -len("/" + PLANS_SUBDIR)]
            ralphex_root = nearest_ralphex(project, stop)
            if ralphex_root is None or ralphex_root in seen:
                continue
            seen.add(ralphex_root)
            actions.append(f"{ralphex_root}: {ensure_link(ralphex_root, plans_dir)}")
        except Exception as exc:  # never break the agent turn
            actions.append(f"{workspace}: error: {exc}")
    return actions


def run_tests() -> int:
    failures: list[str] = []

    def check(name: str, cond: bool) -> None:
        print(f"  {'PASS' if cond else 'FAIL'}: {name}")
        if not cond:
            failures.append(name)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = os.path.realpath(tmp)

        check("payload: malformed JSON", workspace_paths("{not json") == [])
        check("payload: non-object", workspace_paths("[1, 2]") == [])
        check("payload: missing key", workspace_paths("{}") == [])
        check("payload: non-list", workspace_paths('{"workspacePaths": "x"}') == [])
        check(
            "payload: keeps existing dirs only, in order",
            workspace_paths(json.dumps({"workspacePaths": [tmp, 7, "", tmp + "/nope", tmp]}))
            == [tmp, tmp],
        )

        repo = os.path.join(tmp, "repo")
        sub = os.path.join(repo, "sub", "deep")
        os.makedirs(sub)
        check("nearest: none found", nearest_ralphex(sub, repo) is None)
        os.makedirs(os.path.join(repo, ".ralphex"))
        check("nearest: repo root", nearest_ralphex(sub, repo) == repo)
        os.makedirs(os.path.join(repo, "sub", ".ralphex"))
        check("nearest: closest wins", nearest_ralphex(sub, repo) == os.path.join(repo, "sub"))
        check("nearest: never past stop", nearest_ralphex(repo, sub) == repo)
        with open(os.path.join(sub, ".ralphex"), "w") as fh:
            fh.write("file, not dir")
        check(
            "nearest: a .ralphex file does not count",
            nearest_ralphex(sub, repo) == os.path.join(repo, "sub"),
        )

        check(
            "target: sub-project from repo root",
            link_target(repo, os.path.join(repo, "e2e", "docs", "plans")) == "../e2e/docs/plans",
        )
        check("target: same project", link_target(repo, os.path.join(repo, "docs", "plans")) == "../docs/plans")

        plans = os.path.join(repo, "docs", "plans")
        link = os.path.join(repo, ".ralphex", "plans")
        check("link: created when missing", ensure_link(repo, plans).startswith("linked"))
        check("link: is relative symlink", os.readlink(link) == "../docs/plans")
        check("link: plans dir created", os.path.isdir(plans))
        check("link: idempotent", ensure_link(repo, plans).startswith("skip: .ralphex/plans is already"))

        other = os.path.join(tmp, "other")
        os.makedirs(os.path.join(other, ".ralphex", "plans"))
        check("link: empty dir replaced", ensure_link(other, os.path.join(other, "docs", "plans")).startswith("linked"))
        check("link: empty dir is now a symlink", os.path.islink(os.path.join(other, ".ralphex", "plans")))

        full = os.path.join(tmp, "full")
        os.makedirs(os.path.join(full, ".ralphex", "plans"))
        old = os.path.join(full, ".ralphex", "plans", "old.md")
        with open(old, "w") as fh:
            fh.write("old plan")
        check("link: non-empty dir skipped", "holds files" in ensure_link(full, os.path.join(full, "docs", "plans")))
        check("link: old plan untouched", open(old).read() == "old plan")
        check("link: no docs/plans created on skip", not os.path.exists(os.path.join(full, "docs")))

    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        return 1
    print("PASS: all ralphex-plans-link checks passed")
    return 0


def main() -> None:
    if "--test" in sys.argv:
        sys.exit(run_tests())
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    try:
        for line in process(raw):
            log(line)
    except Exception as exc:
        log(f"error: {exc}")
    print("{}")


if __name__ == "__main__":
    main()
