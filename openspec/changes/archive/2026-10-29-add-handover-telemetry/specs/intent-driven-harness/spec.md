# intent-driven-harness Delta

## ADDED Requirements

### Requirement: The harness wires the cc-logging hook
The harness SHALL carry hook groups in the `hooks` object of `.claude/settings.json` for the PreToolUse, PostToolUse, PermissionRequest, SessionStart, SessionEnd, and Stop events. Each new group SHALL run `.claude/hooks/cc-logging.sh`. Each new hook entry SHALL set `timeout` to a positive value and SHALL NOT set `async` to true. The charter group and the spec STE group SHALL stay unchanged. The `.gitignore` file SHALL name the `.cc_logging/` log directory.

#### Scenario: The settings wire the logging hook
- **WHEN** a reader opens `.claude/settings.json`
- **THEN** the six new event groups name the shim path, set `timeout`, and keep `async` false or absent
- **AND** the charter group and the spec STE group stay unchanged

#### Scenario: The log stays uncommitted
- **WHEN** a reader opens `.gitignore`
- **THEN** the file names the `.cc_logging/` directory

### Requirement: The pipeline mandates the telemetry block in handover issues
The `feature-pipeline` skill SHALL carry a Step 13 rule for the telemetry block. The rule tells the agent to build the block with the telemetry CLI and to add it to every handover issue. The template `.github/ISSUE_TEMPLATE/handover.md` SHALL carry a Telemetry section that holds the tool output blocks, and SHALL keep the Task, Logs, Metrics, Observations, and Follow-ups sections.

#### Scenario: A reader finds the Step 13 rule
- **WHEN** a reader scans the `feature-pipeline` skill
- **THEN** the Step 13 handover text names the telemetry CLI and the telemetry block

#### Scenario: The template carries the section
- **WHEN** a reader opens the handover template
- **THEN** a Telemetry section exists next to the five original sections

### Requirement: The pipeline names the shipped logging tooling in Step 14
The `feature-pipeline` skill SHALL name the logging hook and the telemetry CLI as shipped tooling in the Step 14 Log sub-step. The skill SHALL NOT carry the target-design language for the logging surface.

#### Scenario: The Log sub-step names the shipped tooling
- **WHEN** a reader scans the Step 14 text of the `feature-pipeline` skill
- **THEN** the Log sub-step names the hook and the CLI
- **AND** no sentence says that the logging tooling does not exist

## MODIFIED Requirements

### Requirement: The root suite runs in CI
A CI workflow SHALL run the root test suite and the `plan_exec` and `spec_ste_check` lint gates on its pull requests. The workflow SHALL NOT run for changes in `fde/**` or `llm_ops/**` alone. The workflow SHALL run the suite through the registered repository venv interpreter. The workflow SHALL enforce branch coverage of `plan_exec`, `spec_ste_check`, and `handover_telemetry` at a 100 percent floor.

#### Scenario: A pull request triggers the suite
- **WHEN** a pull request changes a file under `tests/`, `tools/`, or `.claude/`
- **THEN** the tests workflow runs the root suite and the coverage and lint gates for all three tools
