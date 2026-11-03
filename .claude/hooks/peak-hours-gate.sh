#!/bin/bash
# peak-hours-gate hook shim.
# Reads one PreToolUse event on standard input and decides it through
# the peak_hours_gate CLI. Exit 2 blocks the call in the z.ai peak
# window. Exit 0 allows. A missing root or a missing interpreter exits
# 0 with no output, so a gate fault never stops a session.
# See openspec/changes/add-peak-hours-gate.

set -u

# Repo root: CLAUDE_PROJECT_DIR when it names the package, else derive
# from $0 (script at <root>/.claude/hooks/), else empty.
ROOT=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/tools/peak_hours_gate" ]; then
  ROOT="$CLAUDE_PROJECT_DIR"
else
  case "$0" in
    */*|*\\*) SCRIPT_DIR="$(cd "${0%[/\\]*}" 2>/dev/null && pwd)" ;;
    *) SCRIPT_DIR="$(pwd)" ;;
  esac
  if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/../../tools/peak_hours_gate" ]; then
    ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  fi
fi

if [ -z "$ROOT" ]; then
  exit 0
fi

# Shared venv interpreter first, system python3 as the fallback.
PY="$ROOT/tools/zai_routing_audit/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || true)"
fi
if [ -z "$PY" ]; then
  exit 0
fi

PYTHONPATH="$ROOT/tools/peak_hours_gate" "$PY" -m peak_hours_gate check
exit $?
