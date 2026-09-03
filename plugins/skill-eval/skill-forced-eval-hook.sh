#!/bin/sh
# skill-forced-eval-hook.sh - PreInvocation hook for AGY/Jetski.
#
# forces the agent to evaluate and activate relevant skills before implementation.

# Note: AGY sends the context payload via stdin. We ignore it here since we
# only want to unconditionally inject an ephemeral message.
cat > /dev/null

cat <<'EOF'
{
  "injectSteps": [
    {
      "ephemeralMessage": "INSTRUCTION: MANDATORY SKILL ACTIVATION\n\nCheck available skills for relevance before proceeding.\n\nIF any skills are relevant:\n  1. State which skills and why (can be multiple)\n  2. Immediately read ALL relevant skills with the view_file tool on their SKILL.md paths\n  3. Then proceed with task\n\nIF no skills are relevant:\n  - Proceed directly\n\nCRITICAL: Read ALL relevant skills via view_file tool before implementation.\nMultiple skills can and should be activated when applicable.\nMentioning a skill without reading its SKILL.md is worthless."
    }
  ]
}
EOF
