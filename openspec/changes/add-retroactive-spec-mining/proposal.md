# Proposal: add-retroactive-spec-mining

## Why

The feature-pipeline rule accretes the specs per change and does not allow a
back-fill. Some live code units have no capability coverage, and archived
deltas can drift from `openspec/specs/`. The tree now holds many tools,
skills, and archived changes. A manual audit of that surface does not scale.

## What Changes

- A new `tools/spec_mining/` package follows the house CLI contract. Pure
  analysis lives in `core.py`. The CLI layer lives in `cli.py` and
  `__main__.py`. The package uses only the stdlib. Exit 0 means success and
  exit 2 means operational failure. The CLI has a `--json` flag. The tool is
  read-only and needs no LLM.
- The working tree miner matches the repo surface (tools, hooks, skills,
  projects) against the capability names in `openspec/specs/`. A committed
  data file in the package holds the aliases and the coverage entries. Bare
  name matching is brittle.
- The archive miner examines the `specs/` delta of each archived change with
  a delta and compares its scenarios with the scenarios in
  `openspec/specs/<capability>/spec.md`. The report names each drift.
- The history miner reads `git log` and ranks each uncovered area by
  merged-commit activity. The read is local.
- Each run writes the directory `reports/spec_mining/<UTC-date>/` with
  `coverage.json`, `report.md`, and one `drafts/<candidate>/proposal.md`
  seed per uncovered capability. The seeds stay outside `openspec/changes/`.
- The `spec-mining` skill at `.claude/skills/spec-mining/SKILL.md` gives the
  commands. The skill starts the normal propose flow from a chosen seed,
  with user approval. The feature-pipeline skill stays unchanged and keeps
  the accretion rule.
- `tests/spec_mining/` covers the three miners, the ranking, and the CLI
  paths.
- CLAUDE.md gains the Projects line for the new tool and skill.
- Non-goals: the tool has no MCP server wrapper. The saturation-pass
  owned-tools table stays at nine entries. The registry gets no new unit,
  because the package is pure stdlib and needs no install.

## Capabilities

### New Capabilities

- `spec-mining`: An opt-in, read-only audit of the spec coverage. It ranks
  the uncovered surface from the tree, the archive, and the git history. It
  reports the archive drift and writes seed proposals for the propose flow.

### Modified Capabilities

- (none)

## Impact

- Code: new `tools/spec_mining/`, new `tests/spec_mining/`, new
  `.claude/skills/spec-mining/`, and run directories under
  `reports/spec_mining/`.
- Specs: the change adds the `specs/spec-mining/` delta. No existing
  capability spec changes.
- Wiring: the new package joins the CI coverage source and the root suite.
  The CRAP, duplication, and mutation gates run on the package. The
  interpreter is the shared venv python when it exists, and the system
  `python3` after that.
- No change to the feature-pipeline skill, any hook, or any gate behavior.
  No workflow calls the tool. Use is opt-in.
- Dependencies: none. The package uses only the stdlib.
- Gates: none. `tools/dspy_gate/dspy_gate/harness/registry.py` declares only
  `ticket-triage`, so this change is ungoverned. The archived residue-scan
  change carries no `gates.yaml` and no `rubrics/`. This change carries none
  either.
- Systems: the tool reads the working tree, `openspec/changes/archive/`, and
  `git log`. It writes only under `reports/`. The seeds are plain files
  outside the spec gates until a propose flow moves one into
  `openspec/changes/`.
