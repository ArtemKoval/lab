# intent-driven-harness Specification (Delta)

## ADDED Requirements

### Requirement: The harness wires the charter hook
The harness SHALL carry a `hooks` object in `.claude/settings.json` with a `SessionStart` group whose matcher is `startup|clear|compact` and whose command runs `.claude/hooks/harness-charter.sh`. The hook entry SHALL set `timeout` to a positive value and SHALL NOT set `async` to true. The sources `resume` and `fork` SHALL stay unmatched, because those sessions replay context that already includes the charter.

#### Scenario: The settings wire the hook
- **WHEN** a reader opens `.claude/settings.json`
- **THEN** a `hooks.SessionStart` group matches `startup|clear|compact`
- **AND** the hook entry names the script path, keeps `async` false or absent, and sets `timeout`
- **AND** the keys `outputStyle`, `enabledMcpjsonServers`, and `permissions` are unchanged

### Requirement: The charter script emits the charter and never fails a session
The script `.claude/hooks/harness-charter.sh` SHALL read `.claude/hooks/charter.md` and SHALL emit exactly one JSON object of the form `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": <charter text>}}` on a session-start event. The script SHALL exit 0 on every outcome. A missing or unreadable charter file SHALL still exit 0 with a one-line fallback context.

#### Scenario: A session start emits the charter
- **WHEN** the script receives a session-start JSON event on standard input
- **THEN** it prints one JSON object whose `hookSpecificOutput.hookEventName` is `SessionStart` and whose `additionalContext` carries the charter text
- **AND** it exits 0

#### Scenario: A missing charter degrades to a fallback
- **WHEN** the script runs and `.claude/hooks/charter.md` does not exist
- **THEN** it prints a one-line fallback context
- **AND** it exits 0

### Requirement: The harness ships the three adoption skills
The harness SHALL provide `systematic-debugging`, `verification-before-completion`, and `writing-skills` under `.claude/skills/`. Each `SKILL.md` SHALL start its `description` with `Use when` and SHALL carry provenance metadata that names `obra/superpowers`, the pinned upstream commit, and the MIT license.

#### Scenario: The adoption skills resolve
- **WHEN** a reader lists `.claude/skills/`
- **THEN** the three directories exist, each with a `SKILL.md` whose `name` matches its directory and whose provenance names the upstream source

### Requirement: The pipeline governs review reception, model selection, and branch finish
The `feature-pipeline` skill SHALL carry: rules for receiving review findings (verify before fix, reasoned pushback, no performative agreement, clarify before fix), a model-selection rule for agent dispatch and the final review, a discard contract that destroys work only after an explicit user confirmation, worktree provenance cleanup rules, and a builder check in the proposal flow. The skill SHALL NOT state that the repo has no hooks after this change lands.

#### Scenario: A reader finds the new pipeline rules
- **WHEN** a reader scans the `feature-pipeline` skill
- **THEN** the review-reception, model-selection, discard-contract, worktree-provenance, and builder-check rules are present

#### Scenario: The stale hooks claim is gone
- **WHEN** a reader scans the `feature-pipeline` skill for a statement that the repo has no hooks
- **THEN** no such statement remains

### Requirement: The adoption decision sits in an accepted ADR
The record `adr/0003-adopt-superpowers-execution-mechanics.md` SHALL exist with accepted status and no `Supersedes:` line, in the house record format of `adr/0001`.

#### Scenario: The record resolves
- **WHEN** a reader opens `adr/0003-adopt-superpowers-execution-mechanics.md`
- **THEN** it carries an accepted status line and no `Supersedes:` line

### Requirement: The root suite runs in CI
A CI workflow SHALL run the root test suite and the `plan_exec` lint gate on pull requests that touch the harness, the tests, or the tools, and SHALL NOT run for `fde/**` and `llm_ops/**` changes alone. The workflow SHALL run the suite through the registered repository venv interpreter and SHALL enforce branch coverage of `plan_exec` at a 100 percent floor.

#### Scenario: A pull request triggers the suite
- **WHEN** a pull request changes a file under `tests/`, `tools/`, or `.claude/`
- **THEN** the tests workflow runs the root suite and the `plan_exec` coverage and lint gates
