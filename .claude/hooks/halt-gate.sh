#!/bin/bash
# halt-gate hook shim.
# Reads one PreToolUse event on standard input. When a halt file
# exists at <root>/.claude/halt — in this checkout, or in the primary
# checkout behind a worktree — exit 2 blocks the call and stderr
# carries the reason from the file's first line, the path, and the
# resume instruction. Exit 0 allows. Pure bash plus one local git
# call: the deny needs no interpreter or venv, so a broken tool chain
# cannot disarm the safety control. A missing root exits 0 like the
# peak-hours shim; the settings wiring keeps CLAUDE_PROJECT_DIR set.
# See openspec/changes/add-halt-gate.

set -u

deny() {
  echo "halt-gate: denied — the halt file is present at $1. Reason: $2. Remove the file to resume." >&2
  exit 2
}

reason_of() {
  # Bound the read before the line cut, so a newline-less file cannot
  # push unbounded bytes through the pipe and time the gate out.
  # Carriage returns go, and a line with no readable text yields the
  # fallback reason.
  local text
  text="$(head -c 200 "$1" 2>/dev/null | head -n 1 | tr -d '\r')"
  case "${text//[[:space:]]/}" in
    "") echo "the halt file carries no readable reason" ;;
    *) echo "$text" ;;
  esac
}

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

if [ -n "$ROOT" ] && [ -f "$ROOT/.claude/halt" ]; then
  deny "$ROOT/.claude/halt" "$(reason_of "$ROOT/.claude/halt")"
fi

# A worktree session resolves its own root. Consult the primary
# checkout too, so one halt file stops the loops in every worktree.
COMMON="$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"
if [ -n "$COMMON" ]; then
  PRIMARY="$(dirname "$COMMON")"
  if [ "$PRIMARY" != "$ROOT" ] && [ -f "$PRIMARY/.claude/halt" ]; then
    deny "$PRIMARY/.claude/halt" "$(reason_of "$PRIMARY/.claude/halt")"
  fi
fi

exit 0
