# peak_hours_gate

A stdlib CLI and a Claude Code hook that deny model-backed starts in the
z.ai peak window. The window is Monday to Friday, 14:00 to 18:00
Singapore Standard Time (UTC+8). The start is inclusive and the end is
exclusive.

## Why

The lab routes Claude Code through z.ai GLM, and z.ai charges peak-window
rates. The user rule says: no task starts in the window. A prompt rule
cannot stop a dispatch, so a PreToolUse hook stops it.

## The gate contract

- The hook denies Task, Agent, Workflow, WebSearch, and WebFetch in the
  window with exit code 2.
- It denies every tool whose name starts with `mcp__`.
- It denies a Bash command that runs the dspy_gate optimize, certify,
  evals, or nightly subcommand.
- It allows chat, plan mode, file edits, and SendMessage. SendMessage
  continues work that an earlier dispatch started.
- The deny message names the window and the override.
- `ZAI_PEAK_HOURS_OVERRIDE=1` in the session environment bypasses the
  gate. Launch the session with it only for an emergency.
- Internal errors fail open. A gate fault never stops a session.
- The tool reads the current UTC time and adds the 8-hour offset. A
  wrong host clock shifts the window.

## Commands

The suite and CI run the CLI through the shared repository venv:

```bash
PYTHONPATH=tools/peak_hours_gate tools/zai_routing_audit/.venv/bin/python -m peak_hours_gate status
PYTHONPATH=tools/peak_hours_gate tools/zai_routing_audit/.venv/bin/python -m peak_hours_gate status --json
echo '{"tool_name": "Task"}' | PYTHONPATH=tools/peak_hours_gate tools/zai_routing_audit/.venv/bin/python -m peak_hours_gate check
echo '{"tool_name": "Task"}' | PYTHONPATH=tools/peak_hours_gate tools/zai_routing_audit/.venv/bin/python -m peak_hours_gate check --json
```

- `status` reports the window state and the next boundary. It always
  exits 0.
- `check` reads one hook event on stdin. It exits 0 on allow and 2 on
  deny. The deny message goes to stderr. `--json` prints the decision,
  the reason, and the tool name on stdout.
- `--now` names one ISO 8601 instant to decide against. A value without
  a zone reads as UTC. The `PEAK_HOURS_GATE_NOW` environment variable
  carries the same value for shim-level tests. Production runs use the
  real clock.

## Tests and gates

The root suite carries the tests at `tests/peak_hours_gate/`:

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest tests/peak_hours_gate tests/claude_infra/test_peak_hours_hook.py
```

The coverage floor, the complexity gate, the duplication gate, and the
mutation gate run on the changed paths the way CI runs them. See
`.github/workflows/tests.yml`.

## Failure routes

- A deny that looks wrong: examine the host clock, then the `status`
  output. The window math lives in `core.py` and takes the instant as a
  parameter.
- A session that must run in the window: use the override variable, and
  say why in the handover issue.
- A gate fault: the shim exits 0 with no output on a missing root or a
  missing interpreter. The `check` path fails open on bad input by
  design.
