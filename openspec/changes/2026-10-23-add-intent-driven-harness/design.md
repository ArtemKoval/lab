# Design

## Context

Facts from reality checks on 2026-10-23:

- `openspec` CLI 1.14.1 is installed and registered as the `openspec-cli` setup unit. `openspec schema which intent-driven` fails today because no project-local schema exists. The only built-in schema is `spec-driven`.
- The schema subcommands use the process working directory as the project root, with no upward search. `openspec schema validate intent-driven` passes at the repo root and fails from any subdirectory. All schema commands in docs, tasks, and tests run from the repo root.
- The six `openspec-*` skills in `.claude/skills/` carry `generatedBy: "1.14.1"`: propose, explore, apply, update, sync, archive. A later `openspec update` regenerates them. Hand edits to those files do not survive. `new` and `continue` have no skill anywhere in this repo.
- The generated skills read artifact instructions and config rules from the active schema through the CLI. A rule like `Must use grill-me skill` surfaces verbatim in the artifact instruction block. A schema switch therefore flows into them without edits.
- `openspec-verify-change` is a CLI-owned skill name: the CLI ships a template with that exact directory name, and the upstream port of it carries `generatedBy: "1.14.0"`. The CLI skips it today only because the core profile filter excludes `verify`. A profile change or CLI update can overwrite a port that keeps the name.
- The template is OpenCode-native: `.opencode/agent/*.md` subagents, `.opencode/skills/`, `.agents/skills/`, `opencode.json`. Claude Code reads `.claude/agents/` and `.claude/skills/` only, requires a `name:` frontmatter field on agent files, and treats `tools:` as an allowlist that defaults to all tools.
- The template pins its own content only by its git history. Head at time of writing: `b5bda460a2180a55fc508fdedc4ef058d95355db` (short form `b5bda460`).
- `tests/claude_infra/test_working_rules.py` computes the repo root from `__file__`, reads files only, and the root suite runs green with the repo venv interpreter. `pytest.ini` adds no coverage or mutation gate, so a docs-and-config change carries no new gate target.
- An archive probe proved that a change authored under `spec-driven` archives cleanly with `intent-driven` active: `openspec archive --yes` synced the delta spec and exited 0.

## Goals / Non-Goals

Goals:

- One intent-driven flow: proposal, Gherkin specs, design, ADR manifest plus durable ADRs, tasks.
- Durable decisions outlive changes in an immutable `adr/` folder.
- Clarification, adversarial authoring, and pre-archive verification available as harness surfaces, not wishes.
- Ports stay faithful to upstream so future template upgrades stay comparable.

Non-Goals:

- No OpenCode compatibility layer. No `.opencode/` or `.agents/` mirrors.
- No `spec-as-source` activation. The skill ships installed but disabled.
- No new gate tooling, dependencies, or setup units.
- No rewrite of the generated `openspec-*` skills; the schema and config carry the new behavior.
- No port of `openspec-new-change`, `openspec-continue-change`, or the two bulk skills. Their flows stay reachable only as raw CLI commands for now.

## Decisions

### D1. Claude Code only, ported into `.claude/`

The lab harness is Claude Code. Keeping `.opencode/` mirrors makes two sources that drift. All ports land under `.claude/skills/` and `.claude/agents/`. `opencode.json` and `skills-lock.json` stay out.

### D2. Schema as pinned project-local files

`openspec/schemas/intent-driven/` (schema, README, five templates) comes from upstream at `b5bda460`. `openspec/config.yaml` switches to `schema: intent-driven`. Every artifact instruction lives in the schema, and the generated skills already read instructions and rules from the schema, so the switch reaches them with no skill edits. This is the Closed World move: the extension point exists, we use it.

`openspec schema validate intent-driven` guards the files. The command runs from the repo root; the test invokes the CLI with `cwd=REPO_ROOT`.

Risk: the schema commands are experimental and the format may drift in a CLI update. Mitigation: the files are project-local and pinned; the validate step fails loud; a CLI upgrade that changes the format becomes a one-change migration.

### D3. Port policy: upstream-verbatim, provenance in frontmatter, recorded adaptations

Ported skill and agent files keep upstream wording and structure. Each ported `SKILL.md` gains a `metadata.ported` block: `from: intent-driven-dev/intent-driven-template`, `commit: b5bda460a2180a55fc508fdedc4ef058d95355db`, `license: MIT`. Ports that reference OpenCode machinery get the minimal mechanical adaptation, and this design records each one:

- Agents (see D4 for the full frontmatter mapping).
- `adversarial-authoring`: "opencode subagents" language becomes Claude Code Agent-tool language. The council-notes format and guardrails stay.
- `openspec-git-discipline`: the gate table keeps its ordering gates verbatim. Lines that ask the user to commit or merge become checkpoints the pipeline executes, because the user's task-level approval is the explicit ask the skill requires. This resolves the clash with the pipeline's autonomous branch, commit, and merge steps.
- `openspec-verify-change`: ported under the new name `verify-change` (directory and frontmatter `name:`), because `openspec-verify-change` is a CLI-owned directory name the CLI can regenerate. The stale `generatedBy: "1.14.0"` metadata drops out; the provenance block replaces it. The D10 provenance test is the real clobber detector.
- `acceptance-test-authoring`: the `stack:` key in `openspec/config.yaml` is a skill-internal convention, not a CLI-parsed key. The references stay; the skill README documents the convention. Cross-references to `spec-as-source` gain a note that the layer is disabled in this harness.

All prose we author ourselves follows ASD-STE100 per CLAUDE.md. CLAUDE.md exempts quoted text and names; vendored upstream files are the quoted-text case. This keeps upstream diffs meaningful.

### D4. Agents

Four files in `.claude/agents/`: `adversarial-author.md`, `adversarial-reviewer.md`, `senior-dev.md`, `senior-qa.md`. Frontmatter mapping from OpenCode:

- Add `name:` matching the file stem. Upstream has no name field; Claude Code silently skips a nameless agent file.
- Keep `description:`.
- The adversarial pair has upstream `permission: {edit: allow, bash: deny}`. Claude Code has no `permission` field, and an omitted `tools:` means all tools. The pair gets an explicit `tools:` allowlist that omits Bash and Edit. `senior-dev` and `senior-qa` get allowlists that keep Bash and Edit, matching their upstream `bash: allow`.
- Drop `mode:`. Do not set `permissionMode:`. No model pin; agents inherit the session model, as upstream intends (upstream comments the model line out).

D7's edits add the `grill-me`, `adversarial-author`, and `adversarial-reviewer` references to the pipeline; they exist nowhere today.

### D5. Skill set and the opt-in map

Eleven independent skill directories under `.claude/skills/`: `grill-me`, `adversarial-authoring`, `architectural-decision-records` (with `preferences.md` and five templates: custom, madr-full, madr-minimal, nygard, y-statement), `c4-diagrams` (with `templates.md`), `gherkin-authoring`, `glossary` (with `README.md`), `openspec-git-discipline`, `verify-change`, `spec-as-source` (with its `references/` tree), `acceptance-test-authoring` (with its `references/` tree: two prose guides, a lint config, four JavaScript files, five Python files), and `test-driven-development` (with two references).

`openspec/config.yaml` rules, adapted from the template's map:

    rules:
      proposal:
        - Must use grill-me skill
        - Must use adversarial-authoring skill
      specs:
        - Must use gherkin-authoring skill
      design:
        - Must use c4-diagrams skill
      adr:
        - Must use architectural-decision-records skill
      tasks:
        # - Must use spec-as-source skill
    operations:
      apply:
        guidance:
          - Must use test-driven-development skill
      archive:
        guidance:
          - Must run OpenSpec Sync before archiving

Disabled and commented, like the template default: `spec-as-source` under `specs` and `tasks`, and `glossary` under `proposal` and `design`. Only `spec-as-source` is a disabled layer; the other ten skills are plain surfaces.

Two departures from the template map, each deliberate: adversarial-authoring is enabled here (the template leaves it commented; decision D7 chose the strict discipline, and proposal review is where authoring bias dies), and gherkin-authoring is enabled under `specs` because the schema's spec format is Gherkin-style.

### D6. Lifecycle skills: one rename-and-port, the rest deferred

The generated set is six skills: propose, explore, apply, update, sync, archive. The template adds verify, new, continue, and two bulk skills. Port `verify-change` only, under its new name (D3). `new` is reachable only inside the propose flow; `openspec continue` stays a raw CLI command. The bulk skills need a parallel-change workflow we do not run yet. Defer all four consciously and say so in the README rather than porting dead weight.

### D7. Git discipline, template-faithful, three merges

Adopt a three-merge flow for every future change, with each merge a reviewed squash-merge PR so no direct push to `main` becomes standing practice:

1. Proposal artifacts (proposal, specs delta, design, adr manifest, tasks, council notes) land on a branch and merge to `main` as the proposal review.
2. Implementation runs on a fresh branch cut from that merge, in its own worktree when an agent drives it. It merges to `main` as the implementation review.
3. Archive runs on a small archive branch (`chore/archive-<change>`) that applies `openspec archive` and the spec sync. It merges to `main` as the archive PR.

Port `openspec-git-discipline` with the D3 checkpoint adaptation. Edit the `feature-pipeline` skill:

- Step 1.5 becomes "Spec (two merges)": write artifacts, review, merge the proposal first. Implementation moves to Step 2 on a new branch in its own worktree.
- Step 13 states: implementation merge first, then the archive branch and its PR.
- Step 12 review applies to the proposal and implementation merges; the proposal merge gets the adversarial lens through the `adversarial-authoring` rule.
- The inner-loop plan review names `grill-me` for clarification and the two adversarial agents for the review round.

CLAUDE.md gains the discipline line and the `adr/` layout entry. This change itself rides the current one-merge pipeline; the new flow starts with the next change.

### D8. ADR folder and first records

`adr/NNNN-kebab-title.md` at the repo root, immutable once accepted, supersession through a `Supersedes:` field only. The durable-record format source is the `adr` artifact instruction in `schema.yaml` (not `templates/adr.md`, which is the change-local review manifest): title, `Status:`, `Date:`, optional `Supersedes:`, and MADR-short sections. Every future change under the new schema also writes its own change-local `adr.md` manifest.

Seed two records now, in the exact syntax the D10 test asserts (`Status: accepted` and no `Supersedes:` line):

- `adr/0001-add-intent-driven-harness.md` — this adoption.
- `adr/0002-claude-code-single-harness.md` — decision D1.

Both records dogfood the ADR flow immediately and give the schema's "read every ADR first" rule real input.

### D9. Glossary seed in the paths the skill reads

The glossary skill reads `glossary/business.md` and `glossary/technical.md` at the repo root. Seed exactly those two files. `business.md` gets the process terms: change, capability, intent, gate, handover. `technical.md` gets the harness terms: ASD-STE100, ASIT, ADR, council notes, spec delta, supersession, harness. The `glossary` skill stays disabled; enabling it later costs one config line.

### D10. Tests: structural, stdlib, hermetic

New module `tests/claude_infra/test_intent_driven_harness.py` runs in the root suite. No new source module exists, so the gates that measure source (coverage floor, mutation score) have no new target; this change adds no production code, and tests prove the wiring instead:

1. Schema: `subprocess.run(["openspec", "schema", "validate", "intent-driven"], cwd=REPO_ROOT, capture_output=True)`, gated on `shutil.which("openspec")`, skipped with a clear message when absent. A stdlib file check asserts the key lines: `name: intent-driven` and the five artifact ids proposal, specs, design, adr, tasks.
2. Agents: exactly the four files exist under `.claude/agents/`, each with non-empty `name:` and `description:` frontmatter, and each `name:` equals its file stem.
3. Skills: every uncommented `Must use <name> skill` line in the enabled rules resolves to a directory under `.claude/skills/`. The provenance block (`ported:` with the pinned commit) exists in every ported `SKILL.md`. The commented `spec-as-source` lines carry `#`. The ADR skill holds `preferences.md` and the five template filenames. The four agent names appear in the ported adversarial-authoring text (closed list, no open prose parsing).
4. ADRs: `adr/0001-add-intent-driven-harness.md` and `adr/0002-claude-code-single-harness.md` exist, each carries a line starting `Status:` and no line starting `Supersedes:`.
5. Glossary: `glossary/business.md` and `glossary/technical.md` exist and name their seeded terms.

### D11. Council notes

Artifacts of this change carry sibling `*.council.md` notes from the adversarial pass, committed with the change, per the ported skill format. The proposal and design notes record this review panel's findings and resolutions.

## Risks / Trade-offs

- [Three merges per change triple review ceremony] -> The pipeline already scales ceremony to risk; the proposal and archive merges stay small because artifacts are short. Accept.
- [Schema format drift on CLI update] -> Pinned local files plus a validate step in tests; migration is one change.
- [A future profile change re-enables `verify` and the CLI regenerates `openspec-verify-change`] -> The port lives under `verify-change`, a name the CLI does not manage. The provenance test detects a clobber either way.
- [Ports drift from upstream over time] -> Provenance metadata plus the verbatim policy makes future template upgrades a reviewable diff.
- [More skills raise context cost per session] -> Skills are description-gated; only the ones a step names get loaded. Eleven directories cost one listing, not eleven loads.

## Migration Plan

1. Land this change on the current pipeline (one merge).
2. The next change runs the three-merge flow and the new rules end to end; its frictions feed the first harness retrospective.
3. Rollback: switch `schema:` back to `spec-driven` in `openspec/config.yaml`. The schema files, skills, agents, and ADRs are inert without the switch.

## Open Questions

- None. The user picked the strict discipline, disabled spec-as-source, and Claude-Code-only on 2026-10-23. The review panel returned no open questions.
