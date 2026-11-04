# Proposal: add-peak-hours-gate

## Why

The lab routes Claude Code through z.ai GLM. z.ai charges peak-hour rates in its peak window. The user set a rule: no task starts in the peak window. A prompt rule does not stop a call. A hook stops the call. This change adds the hook as a static gate.

## What Changes

- Add a static gate that blocks model-backed calls in the peak window. The window is Monday to Friday, 14:00 to 18:00 Singapore Standard Time. The start is inclusive. The end is exclusive. The window uses the UTC+8 offset, with no DST. The tool reads the current UTC time and adds the 8-hour offset.
- Add a bash shim at `.claude/hooks/peak-hours-gate.sh`. Add the PreToolUse hook entry for the shim in `.claude/settings.json`.
- The block set holds Task, Agent, Workflow, WebSearch, and WebFetch. Task, Agent, and Workflow are agent and team dispatches. The block set also holds every tool with the `mcp__` prefix. The block set also holds Bash commands that run the dspy_gate live paths: optimize, certify, evals, and nightly.
- The allow set holds chat, plan mode, file edits, and SendMessage. SendMessage continues work that an earlier dispatch started.
- The gate denies a block-set call with exit code 2. A fail-open run exits 0. The deny message names the window and the override. The override is `ZAI_PEAK_HOURS_OVERRIDE=1` in the hook process environment.
- Internal errors fail open. The gate then allows the call. A gate fault never stops a session. The cc-logging hook uses the same pattern.
- Add the gate tool at `tools/peak_hours_gate/` as a module and a CLI. The CLI has the `check` and `status` subcommands and a `--json` flag.
- Add the tests at `tests/peak_hours_gate/`.
- Add the `peak-hours-gate` skill and the tool README. CLAUDE.md gets the gate rule at the top and a Projects entry.
- The change adds no harness registry entry, no `gates.yaml`, and no `rubrics/`. The dspy-gate system governs only the capabilities that the harness registry declares. An ADR records the window policy at archive.

## Capabilities

### New Capabilities

- `peak-hours-gate`: The gate blocks model-backed calls from Monday to Friday, 14:00 to 18:00 UTC+8, with the start inclusive and the end exclusive. The block set holds agent and team dispatches, web tools, MCP tools, and the dspy_gate live paths. The allow set holds chat, plan mode, file edits, and SendMessage. The gate denies with exit code 2. The deny message names the window and the override. Internal errors fail open, and the fail-open run exits 0.

### Modified Capabilities

- (none)

## Impact

- The tool follows the house layout: `tools/peak_hours_gate/peak_hours_gate/` with `cli.py` and `__main__.py`, plus `pyproject.toml`, `ruff.toml`, and `README.md`.
- The tool uses the Python standard library only. It adds no dependency to any venv.
- The shim at `.claude/hooks/peak-hours-gate.sh` runs the tool module. The interpreter is the shared venv python when it exists, and the system `python3` after that. `tools/project_setup/registry.json` gets no new unit. A clean clone needs no setup step.
- `.claude/settings.json` gains one PreToolUse entry for the shim.
- The tests live at `tests/peak_hours_gate/` and run in the root suite. The CI workflow `tests.yml` gains the `--cov` source, the gated root, and the `.coveragerc` omit line for the tool. The pinned substrings in `tests/claude_infra/test_ci_workflow.py` update with it. The tool joins the default quality gates: CRAP, duplication, and mutation.
- The skill lands at `.claude/skills/peak-hours-gate/`. CLAUDE.md gets the gate rule at the top and a Projects entry.
