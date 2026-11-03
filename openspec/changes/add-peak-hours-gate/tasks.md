# Tasks: add-peak-hours-gate

## 1. The core tool

- [ ] 1.1 Write `tools/peak_hours_gate/peak_hours_gate/core.py`: the pure window math and the block-set decision. The window math is `sgt` and `is_peak`. The decision is `decide` with the injected `now`. `BLOCKED_TOOLS`, `MCP_PREFIX`, and `BASH_LIVE_PATTERNS` stay data. TDD through `tests/peak_hours_gate/`.
- [ ] 1.2 Write `tools/peak_hours_gate/peak_hours_gate/cli.py` and `__main__.py`: the `check` and `status` subcommands. They carry the `--json` and `--now` flags and the `PEAK_HOURS_GATE_NOW` env seam. The exit contract is 0 on allow and 2 on deny, and internal errors fail open. Add `pyproject.toml` and `ruff.toml`.
- [ ] 1.3 Write the deny message contract: exit 2 with a stderr message that names the window and `ZAI_PEAK_HOURS_OVERRIDE`.

## 2. The shim and the wiring

- [ ] 2.1 Write `.claude/hooks/peak-hours-gate.sh`: the root resolve and the interpreter resolve. The shared venv python comes first, and `python3` comes after it. The shim passes stdin through and fails open with no output on a missing root or interpreter.
- [ ] 2.2 Wire the shim in `.claude/settings.json` under PreToolUse. The matcher is `Task|Agent|Workflow|WebSearch|WebFetch|Bash|mcp__.*` with a timeout of 10 seconds. Use the update-config skill.

## 3. Tests and CI wiring

- [ ] 3.1 Write `tests/peak_hours_gate/` to cover every spec scenario. The scenarios span the window boundaries, the block and allow sets, the override, the fail-open paths, the shim contract, and the CLI output. New code reaches 100 percent line and branch coverage.
- [ ] 3.2 Wire CI for the new tool. Add the `--cov` source and the gated root in `.github/workflows/tests.yml`. Add the `.coveragerc` omit line for `__main__.py`. Update the pinned substrings in `tests/claude_infra/test_ci_workflow.py`.
- [ ] 3.3 Add the hook-wiring contract test that reads `.claude/settings.json` and asserts the matcher and the timeout. Follow the `test_spec_ste_hook.py` pattern.

## 4. The quality gates and the surfaces

- [ ] 4.1 Run crapper, dryer, and mutator on the changed paths and make all three green.
- [ ] 4.2 Write `tools/peak_hours_gate/README.md` with the commands and the failure routes.
- [ ] 4.3 Write `.claude/skills/peak-hours-gate/SKILL.md` with the trigger, the CLI commands, the exit codes, and the override rule.
- [ ] 4.4 Add the CLAUDE.md rule at the top of the file in STE form and add the tool to the Projects list.

## 5. The gates and the review

- [ ] 5.1 Run the full hermetic root suite with the shared venv interpreter and make it green.
- [ ] 5.2 Run `openspec validate add-peak-hours-gate --type change --strict`, `dspy_gate lint`, and `dspy_gate verify` before the pull request.
- [ ] 5.3 Verify the deny and allow paths live through the shim with the `PEAK_HOURS_GATE_NOW` seam, and time the hook.
- [ ] 5.4 Run the adversarial whole-diff review, fix the confirmed findings, and publish the fixes before the merge.
