#!/bin/bash
# resolve an absolute project-relative directory (plans, backlog, ...) for the
# project the agent is working in
# usage: resolve-project-dir.sh <subdir> [override]
#   e.g. resolve-project-dir.sh docs/plans '${user_config.plans_dir}'
#        resolve-project-dir.sh docs/backlog
#
# prints <project-root>/<subdir>. a non-empty override replaces <subdir>: an
# absolute override is printed as-is, a relative one resolves against the
# project root. an unexpanded literal ${user_config.*} token counts as unset.
#
# project root: the nearest directory, walking up from the current directory
# and never past the VCS root (git or hg), that contains AGENTS.md, GEMINI.md,
# .agents/ or an existing <subdir>. with no match it is the VCS root; outside
# any VCS it is the current directory, so nothing above it is ever picked up.
# this keeps the directory next to the rules of the project the agent was
# started in, whether that project is a whole repository or a subdirectory of
# a monorepo. nothing about any particular project is encoded here.
#
# never creates the directory. exits 1 only when <subdir> is missing.
#
# this file is shipped byte-identical in every plugin that needs it, so each
# plugin works when installed on its own; tests/test-resolve-project-dir.sh
# fails if the copies drift.

subdir="${1:-}"
if [ -z "$subdir" ]; then
    echo "error: usage: resolve-project-dir.sh <subdir> [override]" >&2
    exit 1
fi

override="${2:-}"
case "$override" in
'${user_config.'*'}') override="" ;;
esac
target="${override:-$subdir}"
target="${target%/}"

case "$target" in
/*)
    echo "$target"
    exit 0
    ;;
esac

start="$(pwd -P)"

stop="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$stop" ] && command -v hg >/dev/null 2>&1; then
    stop="$(hg root 2>/dev/null || true)"
fi
if [ -n "$stop" ]; then
    stop="$(cd "$stop" && pwd -P)"
else
    stop="$start"
fi

root=""
dir="$start"
while :; do
    if [ -f "$dir/AGENTS.md" ] || [ -f "$dir/GEMINI.md" ] || [ -d "$dir/.agents" ] ||
        [ -d "$dir/$target" ]; then
        root="$dir"
        break
    fi
    if [ "$dir" = "$stop" ] || [ "$dir" = "/" ]; then
        break
    fi
    dir="$(dirname "$dir")"
done

echo "${root:-$stop}/$target"
exit 0
