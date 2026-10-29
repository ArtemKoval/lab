#!/bin/bash
# cc-logging hook shim.
# Reads one session event on standard input and appends one redacted
# JSON line to <repo>/.cc_logging/<session-id>.jsonl through the
# handover_telemetry hook module. Always exits 0: a missing root, a
# missing interpreter, or a module error lets the event through with
# no output. See openspec/changes/add-handover-telemetry.

set -u

# Repo root: CLAUDE_PROJECT_DIR when it names the package, else derive
# from $0 (script at <root>/.claude/hooks/), else empty.
ROOT=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/tools/handover_telemetry" ]; then
  ROOT="$CLAUDE_PROJECT_DIR"
else
  case "$0" in
    */*|*\\*) SCRIPT_DIR="$(cd "${0%[/\\]*}" 2>/dev/null && pwd)" ;;
    *) SCRIPT_DIR="$(pwd)" ;;
  esac
  if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/../../tools/handover_telemetry" ]; then
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

PYTHONPATH="$ROOT/tools/handover_telemetry" "$PY" -m handover_telemetry.hook </dev/stdin >/dev/null 2>&1
exit 0
