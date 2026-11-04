# Design: add-peak-hours-gate

## Source

The user asked for the peak-hours rule at the top of CLAUDE.md and a static gate that blocks expensive LLM tasks in the window. A question round settled the block scope (all model-backed calls) and the enforcement mode (deny with an emergency override). One addition: `dspy_gate nightly` joins the blocked live paths because it drives optimize and certify.

## Plan review

The grill round settled four forks. First, the boundary semantics: 14:00 inclusive, 18:00 exclusive. Second, the mid-task entry: the gate blocks starts only. So SendMessage continues work that an earlier dispatch started. Third, the fail-open rule follows the cc-logging precedent. Fourth, the override is the escape hatch for in-window pipeline runs.

The adversarial pair on the proposal folded six findings. They were the missing Capabilities header, the false coverage-floor claim, the capability bullet consistency, the clock source, the interpreter order, and the nightly boundary.

## Diagrams

Format: ASCII in fenced blocks. Rigor: lightweight C4-inspired. Both choices follow the add-dspy-gate precedent.

### Container diagram

```text
+----------------------+
| user                 |
+----------+-----------+
           | prompts, chat, task requests
           v
+------------------------------------------------------------------+
| Claude Code session (the harness container)                      |
|                                                                  |
|   tool call --> PreToolUse event --> hook runner                 |
|                                         | event JSON on stdin    |
|                                         v                        |
|              +----------------------------------------+         |
|              | .claude/hooks/peak-hours-gate.sh       |         |
|              | bash shim: root + interpreter resolve  |         |
|              +--------------------+-------------------+         |
|                                   | python -m peak_hours_gate   |
|                                   v                             |
|              +----------------------------------------+         |
|              | tools/peak_hours_gate (stdlib CLI)     |         |
|              | pure window math + block-set decision  |         |
|              +--------------------+-------------------+         |
|            exit 2 deny <--+         +--> exit 0 allow           |
+---------------------------|-------------------|---------------+
                            v                   v
              the model sees the deny     the tool call runs
              message; the blocked        and its work reaches
              work never reaches          z.ai GLM
              z.ai GLM

+----------------------+          +------------------+
| z.ai GLM (external)  |          | host clock       |
+----------------------+          | (external)       |
                                  +------------------+
```

### Component view inside the tool

```text
+----------------------------------------------------------------+
| tools/peak_hours_gate/peak_hours_gate/                         |
|                                                                |
|  core.py    pure: sgt(dt), is_peak(dt), decide(event, now,     |
|             override) -> (exit_code, message)                  |
|             data: BLOCKED_TOOLS, MCP_PREFIX, BASH_LIVE_PATTERNS|
|  cli.py     argparse: check, status, --json, --now, env seam   |
|  __main__.py the module entry                                  |
+----------------------------------------------------------------+
```

## Decisions

1. Pure core with an injected clock. The core functions take `now` as a parameter. The CLI adds `--now` and reads the `PEAK_HOURS_GATE_NOW` env seam for shim-level tests. Rationale: deterministic tests, and no monkeypatching of module state.
2. The block set lives in data, not in branches. `BLOCKED_TOOLS` holds the tool names, `MCP_PREFIX` holds the `mcp__` prefix, and `BASH_LIVE_WORDS` plus `BASH_PACKAGE_TOKENS` hold the dspy_gate live-path forms. An extension edits one tuple.
3. The fail-open contract: any parse or lookup error returns exit code 0 with no message. A positive in-window match on the block set is the only deny path. This matches the cc-logging charter.
4. The override lives in the hook process environment, so the session launch carries it. The README and the skill document this.
5. No MCP wrapper: the gate is harness-facing, not model-facing, so the pipeline MCP step does not apply. The skill documents the CLI.
6. CI wiring: `tests.yml` adds the `--cov` source and the gated root, `.coveragerc` omits `__main__.py`, and the pinned substrings in `tests/claude_infra/test_ci_workflow.py` update with it.
7. All prose follows STE, and spec text follows the mechanical rule set per ADR 0004.

## Failure modes

- A wrong host clock shifts the window. Accepted, and the README documents it.
- Claude Code snapshots hooks at session start, so the wiring takes effect on the next session after the merge. The skill documents it.
- A Bash pattern can over-match a command that only mentions a live path, for example an echo of the command text. The denial then lands only in the window, and the message explains it. Accepted as rare and harmless.
- The matcher syntax follows the existing `Write|Edit` matcher usage in the same file.
- A pipeline run that starts in the window halts at its first dispatch with the deny message. The run loses no spend, and the override carries an urgent run past the gate.

## Entropy (ASIT)

- Unification: the house hook pattern (shim, settings wiring, tests, skill) hosts the new behavior. No new component kind.
- Multiplication: one more hook shim instance of the existing pattern, parameterized by its tool module.
- Division: pure decision logic in `core.py`, I/O at the shim and the CLI edge.
- No removal candidate exists, and no dependency, registry unit, or MCP server joins.
