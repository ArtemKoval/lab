#!/bin/bash
# halt-gate hook shim.
# Reads one PreToolUse event on standard input. When the halt file
# exists at <root>/.claude/halt, exit 2 blocks the call and stderr
# carries the reason from the file's first line, the path, and the
# resume instruction. Exit 0 allows. Pure bash: the deny needs no
# interpreter, venv, or module, so a broken tool chain cannot disarm
# the safety control. A missing root exits 0 like the peak-hours shim;
# the settings wiring keeps CLAUDE_PROJECT_DIR set.
# See openspec/changes/add-halt-gate.

set -u

ROOT=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/.claude" ]; then
  ROOT="$CLAUDE_PROJECT_DIR"
else
  case "$0" in
    */*|*\\*) SCRIPT_DIR="$(cd "${0%[/\\]*}" 2>/dev/null && pwd)" ;;
    *) SCRIPT_DIR="$(pwd)" ;;
  esac
  if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/../../.claude" ]; then
    ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  fi
fi

if [ -z "$ROOT" ]; then
  exit 0
fi

HALT="$ROOT/.claude/halt"
if [ ! -f "$HALT" ]; then
  exit 0
fi

REASON="$(head -n 1 "$HALT" 2>/dev/null | cut -c1-200)"
if [ -z "$REASON" ]; then
  REASON="the halt file carries no readable reason"
fi
echo "halt-gate: denied — the halt file is present at $HALT. Reason: $REASON. Remove the file to resume." >&2
exit 2
