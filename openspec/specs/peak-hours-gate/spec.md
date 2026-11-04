# peak-hours-gate Specification

## Purpose

The peak-hours gate stops model-backed work in the z.ai peak window. The window is Monday to Friday, 14:00 to 18:00 Singapore Standard Time. Claude Code runs the hook before each block-set dispatch. A blocked call waits until the window closes.

## Requirements

### Requirement: The gate computes the peak window from UTC
The tool SHALL compute Singapore Standard Time as UTC plus 8 hours with a fixed offset. The window SHALL be Monday to Friday, 14:00 to 18:00 SGT. The start SHALL be inclusive. The end SHALL be exclusive. Saturday and Sunday SHALL stay outside the window.

#### Scenario: The window opens at 14:00 SGT
- **WHEN** the tool examines 06:00 UTC on a Monday
- **THEN** the decision reports the in-window state

#### Scenario: The last minute belongs to the window
- **WHEN** the tool examines 09:59 UTC on a Friday
- **THEN** the decision reports the in-window state

#### Scenario: The window closes at 18:00 SGT
- **WHEN** the tool examines 10:00 UTC on a Friday
- **THEN** the decision reports the out-of-window state

#### Scenario: The minute before the window stays open
- **WHEN** the tool examines 05:59 UTC on a Monday
- **THEN** the decision reports the out-of-window state

#### Scenario: The weekend stays open
- **WHEN** the tool examines 07:00 UTC on a Saturday
- **THEN** the decision reports the out-of-window state

#### Scenario: The host zone does not matter
- **GIVEN** a host whose local zone is not UTC
- **WHEN** the tool examines a UTC datetime of 06:00 on a Monday
- **THEN** the decision reports the in-window state

### Requirement: The gate denies the block-set tools in the window
The hook SHALL deny a call to Task, Agent, Workflow, WebSearch, or WebFetch in the window with exit code 2. It SHALL deny every tool whose name starts with `mcp__`. A deny SHALL print a message on stderr that names the window and the override variable.

#### Scenario: A dispatch denies
- **WHEN** a Task call arrives at 15:00 SGT on a Tuesday
- **THEN** the decision is deny with exit code 2
- **AND** stderr names the window and `ZAI_PEAK_HOURS_OVERRIDE`

#### Scenario: An MCP tool denies
- **WHEN** a call names the tool `mcp__zai-routing-audit__usage_report` in the window
- **THEN** the decision is deny with exit code 2

#### Scenario: The same call passes outside the window
- **WHEN** a Task call arrives at 18:00 SGT on a Tuesday
- **THEN** the decision is allow with exit code 0

### Requirement: The gate denies the dspy_gate live paths in the window
The hook SHALL deny a Bash command that runs the dspy_gate optimize, certify, evals, or nightly subcommand in the window.

#### Scenario: A live path denies
- **WHEN** a Bash command runs `python -m dspy_gate optimize` at 15:00 SGT
- **THEN** the decision is deny with exit code 2

#### Scenario: A local subcommand passes
- **WHEN** a Bash command runs `python -m dspy_gate lint` at 15:00 SGT
- **THEN** the decision is allow with exit code 0

### Requirement: The gate allows the allow set
The gate SHALL allow chat, plan mode, file edits, and SendMessage in the window. It SHALL allow every tool outside the block set. Outside the window it SHALL allow every call.

#### Scenario: A file edit passes in the window
- **WHEN** a Write call arrives at 15:00 SGT
- **THEN** the decision is allow with exit code 0

#### Scenario: SendMessage passes in the window
- **WHEN** a SendMessage call arrives at 15:00 SGT
- **THEN** the decision is allow with exit code 0

#### Scenario: An ordinary Bash command passes
- **WHEN** a Bash command runs `git status` at 15:00 SGT
- **THEN** the decision is allow with exit code 0

### Requirement: The override bypasses the gate
The hook SHALL allow a block-set call when `ZAI_PEAK_HOURS_OVERRIDE=1` is in its environment. Any other value SHALL NOT bypass the gate.

#### Scenario: The override allows the call
- **GIVEN** `ZAI_PEAK_HOURS_OVERRIDE=1` in the environment
- **WHEN** a Task call arrives in the window
- **THEN** the decision is allow with exit code 0

#### Scenario: Another value does not bypass
- **GIVEN** `ZAI_PEAK_HOURS_OVERRIDE=0` in the environment
- **WHEN** a Task call arrives in the window
- **THEN** the decision is deny with exit code 2

### Requirement: The gate fails open on internal errors
The gate SHALL exit 0 when it cannot decide: an interpreter missing, malformed JSON on stdin, or a missing tool name. A positive in-window match on the block set SHALL stay the only deny path.

#### Scenario: Malformed input allows
- **WHEN** stdin holds text that is not JSON
- **THEN** the decision is allow with exit code 0

#### Scenario: An event without a tool name allows
- **WHEN** stdin carries JSON without a tool name
- **THEN** the decision is allow with exit code 0

### Requirement: The shim resolves its root and its interpreter
The shim SHALL run the tool module from `tools/peak_hours_gate`. It SHALL prefer the shared venv interpreter and fall back to `python3`. When it finds no root or no interpreter, it SHALL exit 0 and stay silent.

#### Scenario: The fallback interpreter runs the gate
- **GIVEN** a host with `python3` and no repository venv
- **WHEN** the shim runs one block-set event in the window
- **THEN** the decision is deny with exit code 2

#### Scenario: A missing root allows
- **WHEN** the shim finds no repository root
- **THEN** it exits 0 with no output

### Requirement: The CLI exposes the decision and the state
The `check` subcommand SHALL read one hook event on stdin and print the decision. The `--json` flag SHALL give machine-readable output. The `status` subcommand SHALL report the current SGT time, the in-window state, and the next boundary. Exit code 0 SHALL mean allow and 2 SHALL mean deny.

#### Scenario: JSON output parses
- **WHEN** the `check` subcommand runs with `--json` on one event
- **THEN** stdout parses as JSON and carries the decision and the reason

#### Scenario: Status names the next boundary
- **GIVEN** a clock of 15:00 SGT on a Tuesday
- **WHEN** the `status` subcommand runs
- **THEN** the report names the in-window state and 18:00 as the close time

### Requirement: The harness runs the hook on the block tools
The settings file SHALL carry one PreToolUse entry for the shim with a timeout. The matcher SHALL cover Task, Agent, Workflow, WebSearch, WebFetch, Bash, and the `mcp__` tools. It SHALL NOT match Read, Write, or Edit.

#### Scenario: The matcher covers the block set
- **WHEN** the matcher applies to the block tool names and to `mcp__zai-routing-audit__usage_report`
- **THEN** every one of them matches

#### Scenario: The allow tools stay outside the matcher
- **WHEN** the matcher applies to Read, Write, and Edit
- **THEN** none of them matches

#### Scenario: The wiring loads
- **WHEN** the settings file loads
- **THEN** the PreToolUse group names the shim with a timeout of 10 seconds or less
