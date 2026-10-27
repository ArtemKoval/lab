# intent-driven-harness Specification

## Purpose
TBD - created by archiving change 2026-10-23-add-intent-driven-harness. Update Purpose after archive.

## Requirements

### Requirement: The harness resolves the intent-driven schema
The harness SHALL carry the `intent-driven` schema as project-local files under `openspec/schemas/intent-driven/` and SHALL resolve it as the active schema in `openspec/config.yaml`. The schema SHALL define the five artifacts proposal, specs, design, adr, and tasks with their templates.

#### Scenario: Schema validates
- **WHEN** the command `openspec schema validate intent-driven` runs at the repository root on a clone with the openspec CLI installed. The schema commands use the working directory as the project root
- **THEN** the command reports a valid schema and exits 0

#### Scenario: Config names the schema
- **WHEN** a reader opens `openspec/config.yaml`
- **THEN** the first line sets `schema: intent-driven`

### Requirement: The harness ships the four review and build subagents
The harness SHALL carry `adversarial-author`, `adversarial-reviewer`, `senior-dev`, and `senior-qa` as Claude Code subagents under `.claude/agents/`, ported from the pinned template commit with provenance metadata.

#### Scenario: Agents resolve
- **WHEN** the harness lists `.claude/agents/`
- **THEN** the four agent files exist and each carries a non-empty name that matches its file name

### Requirement: The harness ships the eleven ported skills
The harness SHALL carry the eleven ported skills under `.claude/skills/`, each with a `SKILL.md` that carries provenance metadata for the pinned template commit.

#### Scenario: Enabled rules resolve to skills
- **WHEN** the harness reads each uncommented `Must use <name> skill` line in `openspec/config.yaml`
- **THEN** a directory named `<name>` exists under `.claude/skills/`

#### Scenario: The spec-as-source layer stays disabled
- **WHEN** a reader scans the rules in `openspec/config.yaml` for `spec-as-source`
- **THEN** every occurrence sits in a commented line

### Requirement: Changes cross main between lifecycle phases
The harness SHALL enforce the two-merge discipline: proposal artifacts merge to the mainline before apply starts. Implementation merges before archive runs. Archive runs on the mainline. The `feature-pipeline` skill and CLAUDE.md SHALL document the gates.

#### Scenario: Pipeline states both gates
- **WHEN** a reader scans the `feature-pipeline` skill and CLAUDE.md for the discipline
- **THEN** the proposal-before-apply gate and the merge-before-archive gate appear in both files

### Requirement: Durable decisions live in immutable ADR records
The harness SHALL keep accepted ADRs in `adr/NNNN-kebab-title.md` at the repo root. An accepted record SHALL carry a `Status:` field and SHALL change only through a new record whose `Supersedes:` field names it.

#### Scenario: Seed records exist
- **WHEN** a reader lists `adr/`
- **THEN** records `0001-add-intent-driven-harness.md` and `0002-claude-code-single-harness.md` exist with accepted status and no `Supersedes:` field

### Requirement: The glossary seeds live where the glossary skill reads
The harness SHALL seed `glossary/business.md` and `glossary/technical.md` at the repo root with the process and harness terms the glossary skill reads.

#### Scenario: Seed files resolve
- **WHEN** a reader lists `glossary/`
- **THEN** `business.md` and `technical.md` exist and name the seeded terms

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
The harness SHALL carry `systematic-debugging`, `verification-before-completion`, and `writing-skills` under `.claude/skills/`. Each `SKILL.md` SHALL start its `description` with `Use when` and SHALL carry provenance metadata that names `obra/superpowers`, the pinned upstream commit, and the MIT license.

#### Scenario: The adoption skills resolve
- **WHEN** a reader lists `.claude/skills/`
- **THEN** the three directories exist, each with a `SKILL.md` whose `name` matches its directory and whose provenance names the upstream source

### Requirement: The pipeline governs review reception, model selection, and branch finish
The `feature-pipeline` skill SHALL carry rules for receiving review findings (verify before fix, reasoned pushback, no performative agreement, clarify before fix). The skill SHALL carry a model-selection rule for agent dispatch and the final review. The skill SHALL carry a discard contract that destroys work only after an explicit user confirmation. The skill SHALL carry worktree provenance cleanup rules. The skill SHALL carry a builder check in the proposal flow. The skill SHALL NOT state that the repo has no hooks after this change lands.

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
A CI workflow SHALL run the root test suite and the `plan_exec` and `spec_ste_check` lint gates on its pull requests. The workflow SHALL NOT run for changes in `fde/**` or `llm_ops/**` alone. The workflow SHALL run the suite through the registered repository venv interpreter. The workflow SHALL enforce branch coverage of `plan_exec` and `spec_ste_check` at a 100 percent floor.

#### Scenario: A pull request triggers the suite
- **WHEN** a pull request changes a file under `tests/`, `tools/`, or `.claude/`
- **THEN** the tests workflow runs the root suite and the coverage and lint gates for both tools

### Requirement: The harness wires the spec STE hook
The harness SHALL carry a `PreToolUse` group in the `hooks` object of `.claude/settings.json`. The group SHALL match the `Write` and `Edit` tools and SHALL run `.claude/hooks/spec-ste-gate.sh`. The hook entry SHALL set `timeout` to a positive value and SHALL NOT set `async` to true. The existing keys `outputStyle`, `enabledMcpjsonServers`, and `permissions` SHALL stay unchanged.

#### Scenario: The settings wire the STE hook
- **WHEN** a reader opens `.claude/settings.json`
- **THEN** a `hooks.PreToolUse` group matches `Write|Edit`, names the script path, sets `timeout`, and keeps `async` false or absent
- **AND** the keys `outputStyle`, `enabledMcpjsonServers`, and `permissions` stay unchanged
