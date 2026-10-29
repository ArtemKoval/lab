# 0005 - Adopt the ub-mode discipline and quality tools

- Status: accepted
- Date: 2026-10-28

## Context

The delivery pipeline states its quality gates as tool examples, and no tool in the repo measures complexity and coverage together or finds duplicate code. The `unclebob/ub-mode` skill carries a reduced engineering discipline in three phases. It names three deterministic gate tools: crapper (CRAP scores), dryer (structural duplication), and mutator (mutation testing). The tool repos carry 0BSD licenses. The skill repo carries no license file. The user asked to adopt the skill, the three tools, and the important parts of the discipline. Vendored upstream files sit outside the ASD-STE100 prose rule through `openspec/config.yaml`.

## Decision

Adopt the `ub-mode` skill at upstream commit `57a8bdd28e45ed41900ace0bafa2ff76dd9ed70f` as a vendored skill with provenance frontmatter. Its one local section maps the tool names to this repository's commands. Vendor crapper `6fd92c4`, dryer `66ff6d2`, and mutator `a5a0cb8` under `tools/` as owned code. Make them the default gates for new Python changes. The limits are: CRAP of 10 or less, similarity of 0.8 or less, and no surviving mutants. Gate the changed repository Python in CI from diff-derived explicit paths, and run the three vendored suites there. Record provenance in the vendored README notes, the contract tests, and this record. Do not adopt `uml-viewer`. Do not migrate the existing `ruff` and `mutmut` configs in this change, because a follow-up owns that. Rejected options:

- Install from upstream at setup time. A clone build would need the network, and the mutator sibling path would drift.
- Run `--changed` in CI. It reads the working tree, which is clean there, so it gates nothing.
- Run whole-tree mutation on every pull request. Its runtime is unbounded.
- Relocate the vendored suites under `tests/`. That breaks the upstream layout and enters root-suite collection.

## Consequences

Three Python venvs with tree-sitter land under `tools/`. CI gains the vendored suites (6 seconds, 1 second, and 53 seconds measured) and a diff-scoped mutation gate with an explicit worker cap and timeout. The unlicensed skill text ships with attribution under default all-rights-reserved terms. The accepted risk and the replacement plan live in the skill provenance and this record. The replacement plan rewrites the skill in this repository's own words if the risk matters. Two crapper tests fail on hosts without zsh, and CI is the green gate. The first CI runs confirm the dryer exit-code boundary, the runner zsh, and the real mutation budget. The design holds the fallbacks. The pipeline skill gains the three-phase frame, five adopted rules, and two step edits, so the discipline survives compaction like the rest of the charter.
