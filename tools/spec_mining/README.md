# spec_mining

Retroactive OpenSpec spec mining for this repository. One opt-in,
read-only run names the live units without capability coverage, the
archived deltas that drifted from `openspec/specs/`, and the merged
commit weight of each uncovered area. The tool uses only the Python
standard library and runs no model.

## What one run does

- **Tree scan.** Walks `tools/`, `.claude/hooks/`, `.claude/skills/`, and
  the project directories. A unit is covered when its normalized name
  matches a capability, when a `units.json` alias maps it to one, or when
  its `units.json` coverage entry matches the capability set.
- **Archive drift scan.** Parses the `ADDED` and `MODIFIED` scenario names
  of each archived change delta and reports the names the capability spec
  does not hold today. An archived change with no delta stays out. A
  capability with no spec directory marks its scenarios.
- **History ranking.** One `git log --name-only --format=%H main` call
  feeds the merged commit count per uncovered area. Ties order by area
  name.

## Output

A run writes `reports/spec_mining/<UTC-date>/`:

- `coverage.json` — one payload with the `tree`, `drift`, and `ranking`
  sections.
- `report.md` — the human summary of the same result.
- `drafts/<candidate>/proposal.md` — one evidence-bearing seed scaffold
  per uncovered candidate. Seeds stay outside `openspec/changes/`; the
  propose flow adopts one at a time with user approval.

A rerun replaces the files the run owns (`coverage.json`, `report.md`,
`drafts/`) and leaves any other file in the run directory in place.

## Commands

```bash
PYTHONPATH=tools/spec_mining tools/zai_routing_audit/.venv/bin/python -m spec_mining run
PYTHONPATH=tools/spec_mining tools/zai_routing_audit/.venv/bin/python -m spec_mining run --json
```

The interpreter falls back to the system `python3`. Exit 0 on a completed
run and 2 on a failed fact call, with the reason on stderr and an empty
stdout.

## Data file

`spec_mining/units.json` holds three maps: `aliases` (unit path to
capability name), `projects` (project directory to capability globs), and
`coverage` (unit path to capability or glob list). The operator owns the
file. `tests/spec_mining/test_spec_mining_units.py` fails on a stale
entry or an unresolved capability reference.

## Tests and gates

```bash
tools/zai_routing_audit/.venv/bin/python -m pytest tests/spec_mining
```

The tests inject the runner and fabricate the tree, so they run
hermetic. The quality gates (CRAP at 10 or less, duplication under 0.8,
mutation with no survivors) run over the package on every pull request
that touches it.

## Mutation run

Run the mutator on an out-of-tree copy of this directory, never inside
the repository. See the `ub-mode` skill and the `feature-pipeline` skill
for the gate contract.

## Known gaps

- The first run names `spec_mining` itself as uncovered, because its
  capability spec lands at archive time.
- `notebooks`, `apple`, and `configs` have no capability specs, so the
  tree scan reports them uncovered until specs or coverage entries land.
