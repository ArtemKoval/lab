# intent-driven-harness Specification

## Purpose
TBD - created by archiving change 2026-10-23-add-intent-driven-harness. Update Purpose after archive.

## Requirements

### Requirement: The harness resolves the intent-driven schema
The harness SHALL carry the `intent-driven` schema as project-local files under `openspec/schemas/intent-driven/` and SHALL resolve it as the active schema in `openspec/config.yaml`. The schema SHALL define the five artifacts proposal, specs, design, adr, and tasks with their templates.

#### Scenario: Schema validates
- **WHEN** the command `openspec schema validate intent-driven` runs at the repository root on a clone with the openspec CLI installed (the schema commands use the working directory as the project root)
- **THEN** the command reports a valid schema and exits 0

#### Scenario: Config names the schema
- **WHEN** a reader opens `openspec/config.yaml`
- **THEN** the first line sets `schema: intent-driven`

### Requirement: The harness ships the four review and build subagents
The harness SHALL provide `adversarial-author`, `adversarial-reviewer`, `senior-dev`, and `senior-qa` as Claude Code subagents under `.claude/agents/`, ported from the pinned template commit with provenance metadata.

#### Scenario: Agents resolve
- **WHEN** the harness lists `.claude/agents/`
- **THEN** the four agent files exist and each carries a non-empty name that matches its file name

### Requirement: The harness ships the eleven ported skills
The harness SHALL provide the eleven ported skills under `.claude/skills/`, each with a `SKILL.md` that carries provenance metadata for the pinned template commit.

#### Scenario: Enabled rules resolve to skills
- **WHEN** the harness reads each uncommented `Must use <name> skill` line in `openspec/config.yaml`
- **THEN** a directory named `<name>` exists under `.claude/skills/`

#### Scenario: The spec-as-source layer stays disabled
- **WHEN** a reader scans the rules in `openspec/config.yaml` for `spec-as-source`
- **THEN** every occurrence sits in a commented line

### Requirement: Changes cross main between lifecycle phases
The harness SHALL enforce the two-merge discipline: proposal artifacts merge to the mainline before apply starts, implementation merges before archive runs, and archive runs on the mainline. The `feature-pipeline` skill and CLAUDE.md SHALL document the gates.

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
