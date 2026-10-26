#!/bin/bash
# SessionStart charter hook.
# Reads .claude/hooks/charter.md and emits the SessionStart context
# envelope. Builtins only after bash starts, so a broken PATH cannot
# break the run. Always exits 0; a missing charter degrades to one
# fallback line. See openspec/changes (adopt-superpowers-harness-upgrades).

set -u

# Repo root: CLAUDE_PROJECT_DIR when it names the charter, else derive
# from $0 (script at <root>/.claude/hooks/), else the working directory.
ROOT=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -r "$CLAUDE_PROJECT_DIR/.claude/hooks/charter.md" ]; then
  ROOT="$CLAUDE_PROJECT_DIR"
else
  case "$0" in
    */*|*\\*) SCRIPT_DIR="$(cd "${0%[/\\]*}" 2>/dev/null && pwd)" ;;
    *) SCRIPT_DIR="$(pwd)" ;;
  esac
  if [ -n "$SCRIPT_DIR" ] && [ -r "$SCRIPT_DIR/../../.claude/hooks/charter.md" ]; then
    ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  fi
fi

if [ -n "$ROOT" ]; then
  charter="$(<"$ROOT/.claude/hooks/charter.md")"
else
  charter="The harness charter is unavailable. Follow CLAUDE.md and the feature-pipeline skill."
fi

# JSON-escape with one C-level pass per character class.
esc="${charter//\\/\\\\}"
esc="${esc//\"/\\\"}"
esc="${esc//$'\n'/\\n}"
esc="${esc//$'\r'/\\r}"
esc="${esc//$'\t'/\\t}"

# One top-level object only: the harness reads hookSpecificOutput, and a
# second context field would inject the charter twice.
printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$esc"
exit 0
