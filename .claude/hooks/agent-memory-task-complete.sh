#!/bin/bash
# PostToolUse task-completion nudge for the agent-memory skill (issue #86).
#
# Fires when a Bash call just executed a merge — the canonical task
# completion act in this harness (direct `gh pr merge` or the sanctioned
# wrapper `scripts/evolve-all/safe-merge`). With a valid memory config it
# injects ONE additionalContext line next to the tool result, telling the
# agent to close the memory loop for the bound thread now (skill Mode 3):
# session summary, lesson distillation, cache regeneration. The operator
# never types memory updates.
#
# The injected string is FIXED — the command line is matched, never echoed,
# so nothing from the payload can reach the conversation through this hook.
# Silent on every other command and on any missing or invalid input.
# Surface verified against the hooks reference: PostToolUse
# hookSpecificOutput.additionalContext is delivered next to the tool result.
#
# Pure local: one stdin read, jq-first with grep fallback, one conf read.
# Always exits 0; fails open.

set -u

INPUT="$(cat 2>/dev/null)" || INPUT=""

CMD=""
if command -v jq >/dev/null 2>&1; then
  CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")
fi
if [ -z "$CMD" ]; then
  CMD=$(printf '%s' "$INPUT" | grep -o '"command":"[^"]*"' | head -1 | cut -d'"' -f4 2>/dev/null || echo "")
fi

# Line-anchored match: the merge phrase must start a line or follow a
# command separator. Prose that merely mentions "gh pr merge" (commit
# messages, heredocs, greps) does not trigger the nudge — demonstrated by
# this very skill's own commit messages.
MATCHES=0
while IFS= read -r line; do
  case "$line" in
    "gh pr merge "*|*"&& gh pr merge "*|*"; gh pr merge "*|*"| gh pr merge "*|*=[0-9]*" gh pr merge "*) MATCHES=1 ;;
    "bash "*|*"&& bash "*|*"; bash "*|*=[0-9]*" bash "*)
      case "$line" in
        *evolve-all/safe-merge.sh*) MATCHES=1 ;;
      esac ;;
  esac
  [ "$MATCHES" = "1" ] && break
done <<EOF
$CMD
EOF
[ "$MATCHES" = "1" ] || exit 0

CONF="${HOME:-}/.config/memory-kit.conf"
[ -r "$CONF" ] || exit 0

REPO=""
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in
    MEMORY_REPO=*) REPO="${line#MEMORY_REPO=}" ;;
  esac
done < "$CONF"

case "$REPO" in
  */*) : ;;
  *) exit 0 ;;
esac
OWNER="${REPO%%/*}"
NAME="${REPO#*/}"
case "$OWNER" in
  ""|*[!A-Za-z0-9_.-]*) exit 0 ;;
esac
case "$NAME" in
  ""|*[!A-Za-z0-9_.-]*|*/*) exit 0 ;;
esac

CTX="That merge completed a task. Close the agent-memory loop for the bound thread now (agent-memory skill, Mode 3): write the session summary on the thread, distill lessons, regenerate the cache. No operator prompt is needed; if the store is unreachable, say so and continue."

esc="${CTX//\\/\\\\}"
esc="${esc//\"/\\\"}"
esc="${esc//$'\n'/\\n}"
esc="${esc//$'\r'/\\r}"
esc="${esc//$'\t'/\\t}"

printf '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' "$esc"
exit 0
