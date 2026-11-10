# Proposal: add-session-statusline

## Why

The Claude Code console shows no session cost or quota picture on this
host. The operator watches the z.ai credit pools, the session cache
health, and the token burn across 1-1 sessions, and today that needs
three separate commands. Claude Code 2.1.322 renders a custom status
line from a command that receives a session payload on stdin. The
payload carries the model, the effort level, the prompt-cache ratio,
and the rate-limit windows when the gateway sets them.

## What Changes

### The status line tool

A new stdlib CLI at `tools/session_statusline/` reads the status line
payload on stdin and renders one line: the model, the thinking effort,
the 5-hour and weekly limit percentages, the session cache rate, the
input and output token totals in millions, and the time in UTC. The
payload is the first source for every field. The session transcript
backs the token totals and the cache rate. The `usage` command of
`zai_routing_audit` backs the limit percentages behind a 300 second
cache, and the stale cache wins over a failed read.

### The settings wiring

`.claude/settings.json` gains the `statusLine` block with a 15 second
refresh interval. The command runs the tool through the shared
repository venv with absolute paths. The file is a protected gate
path, so the implementation pull request carries the
`gate-integrity: acknowledged` line.

## Capabilities

### New Capabilities

- `session-statusline`: the rendered line, the field fallbacks, and
  the fail-open behavior.

### Modified Capabilities

None.

## Out of scope

- No change to the Claude Code binary. The status line is the
  documented extension point.
- No per-call provider requests. The tool caches the console read and
  time-boxes the call, and a failed read never blocks the line.
- No user-level settings change. The line renders in this
  repository's sessions only.

## Impact

- `tools/session_statusline/session_statusline.py`: the new tool.
- `tests/session_statusline/`: the unit and contract tests.
- `.claude/settings.json`: the `statusLine` block.
- `CLAUDE.md`: one Projects line for the tool.
- `tools/project_setup/registry.json`: a setup unit for the wiring
  doctor.
- `tools/session_statusline_setup/session_statusline_setup.py`: the
  setup doctor for the wiring unit.
- `tools/session_statusline/README.md`: the tool README.
- `.github/workflows/tests.yml`: the gate whitelist, the coverage
  sources, and the mutator paths gain the two new tool directories,
  behind the operator acknowledgment.
- The tool calls the `usage` command of `zai_routing_audit` with a
  timeout for the console fallback. It calls no program other than
  that one.
