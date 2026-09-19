#!/bin/bash
# run external code review and return findings on stdout
# usage: run-external-review.sh "<external_review_cmd>" "<prompt>"
#
# with an empty or unconfigured <external_review_cmd>, exits 127 with a marker
# so the orchestrator skips the phase. with a command set, that command is run
# with the prompt appended as the final argv element.
#
# exits 127 when the tool is not configured or not on PATH so the caller can skip
# the phase rather than treat it as a review failure. those messages carry
# the marker "run-external-review:" on stderr, so a 127 raised by the reviewer
# itself (a wrapper script whose inner tool is missing) stays distinguishable from
# this one. nothing else written here may carry the marker.

set -e

cmd="$1"
prompt="$2"

if [ -z "$prompt" ]; then
    echo "error: usage: run-external-review.sh '<external_review_cmd>' '<prompt>'" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Unconfigured config token fallback (handles literal ${user_config.KEY} when unexpanded)
# shellcheck disable=SC2016
case "$cmd" in
    '${user_config.'*'}')
        cmd=""
        ;;
esac

# a newline would be swallowed by the single `read` below, running a truncated
# command instead of the configured one -- report it rather than truncate silently
case "$cmd" in
    *$'\n'*)
        echo "error: external_review_cmd must be a single line" >&2
        exit 1
        ;;
esac

# split on whitespace so a command carrying flags works, e.g.
# "mytool review --strict". arguments containing spaces are not supported --
# wrap anything that needs quoting in a script and point the config at it.
read -ra cmd_args <<< "$cmd"

if [ "${#cmd_args[@]}" -eq 0 ]; then
    echo "error: run-external-review: external_review_cmd is not set" >&2
    exit 127
fi

if ! command -v "${cmd_args[0]}" > /dev/null 2>&1; then
    echo "error: run-external-review: external_review_cmd not on PATH: ${cmd_args[0]}" >&2
    exit 127
fi

# exec so a kill on the background task reaches the reviewer rather than a wrapper shell.
# stdin from /dev/null: an inherited open pipe (background launch) would let a
# tool that reads stdin block forever
exec "${cmd_args[@]}" "$prompt" < /dev/null
