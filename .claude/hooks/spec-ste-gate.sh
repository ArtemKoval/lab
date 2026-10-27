#!/bin/bash
# PreToolUse STE gate hook.
# Blocks a Write or Edit on a spec path when the post-edit text carries
# a mechanical ASD-STE100 error. Fails open: a missing root, a missing
# interpreter, or a checker crash lets the write through, and the pytest
# gate stays the backstop. Builtin-only resolution after bash starts, so
# a broken PATH cannot break the run. See openspec/changes/enforce-ste-in-specs.

set -u

# Repo root: CLAUDE_PROJECT_DIR when it names the package, else derive
# from $0 (script at <root>/.claude/hooks/), else empty.
ROOT=""
if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR/tools/spec_ste_check" ]; then
  ROOT="$CLAUDE_PROJECT_DIR"
else
  case "$0" in
    */*|*\\*) SCRIPT_DIR="$(cd "${0%[/\\]*}" 2>/dev/null && pwd)" ;;
    *) SCRIPT_DIR="$(pwd)" ;;
  esac
  if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/../../tools/spec_ste_check" ]; then
    ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
  fi
fi

if [ -z "$ROOT" ]; then
  echo "spec-ste-gate: repository root not found; the write passes" >&2
  exit 0
fi

PY="$ROOT/tools/zai_routing_audit/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY="$(command -v python3 || true)"
fi
if [ -z "$PY" ]; then
  echo "spec-ste-gate: no interpreter found; the write passes" >&2
  exit 0
fi

PYTHONPATH="$ROOT/tools/spec_ste_check" "$PY" -m spec_ste_check.hook
code=$?
# Only 0 (pass) and 2 (block) are gate verdicts. Anything else is a
# checker failure: the write passes, with a note.
if [ "$code" -ne 0 ] && [ "$code" -ne 2 ]; then
  echo "spec-ste-gate: the checker failed; the write passes" >&2
  exit 0
fi
exit "$code"
