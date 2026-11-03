#!/bin/bash
# PostToolUse spec-gates bridge hook.
# After a Write or Edit under openspec/changes/<id>/specs/, runs the
# fast staleness check for that change and injects the regeneration
# command as context when the generated artifacts went stale. Never
# blocks: the hook always exits 0. See openspec/changes/add-dspy-gate.

set -u

ROOT=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/tools/dspy_gate" ]; then
  ROOT="$CLAUDE_PROJECT_DIR"
else
  case "$0" in
    */*|*\\*) SCRIPT_DIR="$(cd "${0%[/\\]*}" 2>/dev/null && pwd)" ;;
    *) SCRIPT_DIR="$(pwd)" ;;
  esac
  if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/../../tools/dspy_gate" ]; then
    ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  fi
fi

if [ -z "$ROOT" ]; then
  echo "spec-gates-bridge: repository root not found; the check passes" >&2
  exit 0
fi

PY="$ROOT/tools/zai_routing_audit/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || true)"
fi
if [ -z "$PY" ]; then
  echo "spec-gates-bridge: no interpreter found; the check passes" >&2
  exit 0
fi

PYTHONPATH="$ROOT/tools/dspy_gate" "$PY" -m dspy_gate.bridge_hook
exit $?
