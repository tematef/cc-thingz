#!/bin/sh
# skill-forced-eval-hook.sh - PreInvocation hook for AGY/Jetski.
#
# forces the agent to evaluate and activate relevant skills before implementation.
#
# PreInvocation fires before every model call of a turn, including the call
# that follows each tool result. The instruction only helps once per turn;
# repeated after every tool call, it makes agents re-check and re-read skills
# mid-task. So it is injected on the first model call of each turn only.
#
# AGY sends the same executionId for every model call of one turn and a new
# one when a turn starts (a user message, or a new message to a subagent).
# The last executionId seen is kept per conversation in a small state file.
# initialNumSteps, which is also constant within a turn, is the fallback key.
# If the payload has neither, or the state cannot be written, the hook
# injects on every call as before.

payload=$(cat | tr -d '\n')

field() {
  # first string or number value of a top-level JSON key, quotes stripped
  printf '%s' "$payload" |
    sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\{0,1\}\([A-Za-z0-9._-]*\).*/\1/p"
}

inject() {
  cat <<'EOF'
{
  "injectSteps": [
    {
      "ephemeralMessage": "INSTRUCTION: MANDATORY SKILL ACTIVATION\n\nCheck available skills for relevance before proceeding.\n\nIF any skills are relevant:\n  1. State which skills and why (can be multiple)\n  2. Immediately read ALL relevant skills with the view_file tool on their SKILL.md paths\n  3. Then proceed with task\n\nIF no skills are relevant:\n  - Proceed directly\n\nCRITICAL: Read ALL relevant skills via view_file tool before implementation.\nMultiple skills can and should be activated when applicable.\nMentioning a skill without reading its SKILL.md is worthless."
    }
  ]
}
EOF
  exit 0
}

conversation=$(field conversationId)
turn=$(field executionId)
[ -n "$turn" ] || turn="steps-$(field initialNumSteps)"
[ -n "$conversation" ] && [ "$turn" != "steps-" ] || inject

state_dir="${CC_THINGZ_SKILL_EVAL_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/cc-thingz/skill-eval}"
mkdir -p "$state_dir" 2>/dev/null || inject
state_file="$state_dir/$conversation"

if [ -f "$state_file" ] && [ "$(cat "$state_file" 2>/dev/null)" = "$turn" ]; then
  echo '{}'
  exit 0
fi

{ printf '%s\n' "$turn" >"$state_file"; } 2>/dev/null || inject
# one small file per conversation; drop the ones idle for a week
find "$state_dir" -type f -mtime +7 -exec rm -f {} + 2>/dev/null
inject
