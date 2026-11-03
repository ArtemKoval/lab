#!/bin/bash
# PreToolUse spec-gates protect hook.
# Denies a Write or Edit on a GENERATED artifact path: the eval
# manifest, the change and frozen evals, the certification ledger, the
# generated conformance module, and the optimizer artifacts. The
# visual baselines stay exempt: a human authors them in the change
# pull request. Fails open: a missing root or interpreter lets the
# write through, and CI stays the backstop. See openspec/changes/add-dspy-gate.

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
  echo "spec-gates-protect: repository root not found; the write passes" >&2
  exit 0
fi

PY="$ROOT/tools/zai_routing_audit/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || true)"
fi
if [ -z "$PY" ]; then
  echo "spec-gates-protect: no interpreter found; the write passes" >&2
  exit 0
fi

PYTHONPATH="$ROOT/tools/dspy_gate" "$PY" -m dspy_gate.protect_hook
exit $?
