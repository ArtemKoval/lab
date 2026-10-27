# intent-driven-harness Specification (Delta)

## MODIFIED Requirements

### Requirement: The root suite runs in CI
A CI workflow SHALL run the root test suite and the `plan_exec` and `spec_ste_check` lint gates on its pull requests. The workflow SHALL NOT run for changes in `fde/**` or `llm_ops/**` alone. The workflow SHALL run the suite through the registered repository venv interpreter. The workflow SHALL enforce branch coverage of `plan_exec` and `spec_ste_check` at a 100 percent floor.

#### Scenario: A pull request triggers the suite
- **WHEN** a pull request changes a file under `tests/`, `tools/`, or `.claude/`
- **THEN** the tests workflow runs the root suite and the coverage and lint gates for both tools

## ADDED Requirements

### Requirement: The harness wires the spec STE hook
The harness SHALL carry a `PreToolUse` group in the `hooks` object of `.claude/settings.json`. The group SHALL match the `Write` and `Edit` tools and SHALL run `.claude/hooks/spec-ste-gate.sh`. The hook entry SHALL set `timeout` to a positive value and SHALL NOT set `async` to true. The existing keys `outputStyle`, `enabledMcpjsonServers`, and `permissions` SHALL stay unchanged.

#### Scenario: The settings wire the STE hook
- **WHEN** a reader opens `.claude/settings.json`
- **THEN** a `hooks.PreToolUse` group matches `Write|Edit`, names the script path, sets `timeout`, and keeps `async` false or absent
- **AND** the keys `outputStyle`, `enabledMcpjsonServers`, and `permissions` stay unchanged
