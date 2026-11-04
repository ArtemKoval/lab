---
name: peak-hours-gate
description: Read and work with the z.ai peak-hours gate. Use this skill when a tool call gets denied in the z.ai peak window, when the user asks about the peak window or its boundaries, when you must bypass the gate for an emergency, or when you extend the block set. Gives the commands, the exit codes, the override rule, and the failure routes.
---

# peak-hours-gate

The hook at `.claude/hooks/peak-hours-gate.sh` denies model-backed starts
Monday to Friday, 14:00 to 18:00 SGT (UTC+8). The tool at
`tools/peak_hours_gate/` owns the window math and the decision. The
wiring sits under `hooks` in `.claude/settings.json`.

## What the gate denies

In the window: Task, Agent, and Workflow dispatches, WebSearch, WebFetch,
every tool whose name starts with `mcp__`, and Bash commands that run
the dspy_gate optimize, certify, evals, or nightly subcommand. The allow
set holds chat, plan mode, file edits, and SendMessage.

## Exit codes

- 0 on allow. The hook prints nothing.
- 2 on deny. The stderr message names the window and the override.
- 0 on any internal error. The gate fails open by design, so a gate
  fault never stops a session.

## Commands

```bash
PYTHONPATH=tools/peak_hours_gate tools/zai_routing_audit/.venv/bin/python -m peak_hours_gate status
echo '{"tool_name": "Task"}' | PYTHONPATH=tools/peak_hours_gate tools/zai_routing_audit/.venv/bin/python -m peak_hours_gate check
```

`--json` gives machine-readable output. `--now` and the
`PEAK_HOURS_GATE_NOW` variable inject the clock for tests. The tests sit
at `tests/peak_hours_gate/` and `tests/claude_infra/test_peak_hours_hook.py`.

## The override

`ZAI_PEAK_HOURS_OVERRIDE=1` in the session environment bypasses the gate.
The hook reads its own process environment, so set the variable when you
launch the session. Use it only for an emergency, and say why in the
handover issue.

## Session timing

Claude Code snapshots hooks at session start. The wiring reaches a
session that starts after the merge. A run that starts in the window
halts at its first dispatch with the deny message, and work that crosses
the boundary stops at its next dispatch.

## How to extend the block set

The block set lives as data in `tools/peak_hours_gate/peak_hours_gate/core.py`:
`BLOCKED_TOOLS`, `MCP_PREFIX`, and `BASH_LIVE_WORDS`. An extension edits
one constant and adds one test. A window or scope change goes through a
new OpenSpec change and a superseding ADR, not a code-only edit.
