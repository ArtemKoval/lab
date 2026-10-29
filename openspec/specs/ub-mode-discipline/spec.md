# ub-mode-discipline Specification

## Purpose

TBD - created by archiving change adopt-ub-mode. Update Purpose after archive.

## Requirements

### Requirement: The ub-mode skill resolves with provenance
The repository SHALL carry `.claude/skills/ub-mode/SKILL.md`. The frontmatter SHALL set `name: ub-mode`. The description SHALL carry the `Use when` trigger and SHALL name `/ub-mode` and the reduced principles. The provenance SHALL carry `from: unclebob/ub-mode`, the pinned commit `57a8bdd28e45ed41900ace0bafa2ff76dd9ed70f`, and a license note that names the unlicensed upstream.

#### Scenario: The skill resolves
- **WHEN** a reader opens `.claude/skills/ub-mode/SKILL.md`
- **THEN** the frontmatter sets `name: ub-mode`, carries the `Use when` trigger, and pins the upstream commit and the license note

### Requirement: The skill body stays upstream plus one local section
The body SHALL stay the upstream text, plus one local section. The local section SHALL map the upstream tool names to the vendored commands of this repository and SHALL record that `uml-viewer` stays out.

#### Scenario: The local section names the vendored commands
- **WHEN** a reader follows the local gates section
- **THEN** it names the vendored crapper, dryer, and mutator commands and their thresholds
- **AND** it states that the repository does not adopt `uml-viewer`

### Requirement: The pipeline carries the adopted discipline
The feature-pipeline skill SHALL carry a subsection under the cross-cutting rules. The subsection SHALL state the three-phase frame: First Make it Work, Then Make it Right, Practice. It SHALL carry the rules the pipeline lacks. The rules cover one decision in one place, data shape before logic, redesign from first principles, attack the premise, and subtract before you add.

#### Scenario: The subsection resolves
- **WHEN** a reader opens the feature-pipeline skill
- **THEN** the cross-cutting rules carry the three-phase frame and the five rules

### Requirement: The pipeline steps carry the test and commit rules
Step 3 SHALL extend its present test wording with the rule to discard a test that still passes when every function returns nothing. Step 10 SHALL carry the rule that each commit says why, what changed, and how you proved it. The contract tests SHALL pin each addition.

#### Scenario: The step edits resolve
- **WHEN** a reader examines Step 3 and Step 10 of the pipeline
- **THEN** Step 3 carries the discard rule and Step 10 carries the commit message rule
- **AND** the contract tests assert both additions
