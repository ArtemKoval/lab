---
name: spec-mining
description: Mine the repository retroactively for OpenSpec coverage. Use when the user asks to mine specs, to name the capabilities without coverage, to find the archived deltas that drifted from openspec/specs/, or to turn mined evidence into a spec proposal.
---

# spec-mining

The tool at `tools/spec_mining/` audits the repository against
`openspec/specs/` in one read-only run. The tree scan matches the tools,
the hooks, the skills, and the projects against the capability names
through a name rule and the committed `units.json` data file. The drift
scan compares the `ADDED` and `MODIFIED` scenario names of every archived
delta with the scenarios the capability spec holds today. The history
ranking counts the merged commits per uncovered area from one `git log`
call.

## Commands

```bash
VENV=tools/zai_routing_audit/.venv/bin/python
PYTHONPATH=tools/spec_mining $VENV -m spec_mining run
PYTHONPATH=tools/spec_mining $VENV -m spec_mining run --json
```

When the shared venv does not exist, run the same commands with the
system `python3` in place of `$VENV`.

## Reading the report

A run writes `reports/spec_mining/<UTC-date>/` with three kinds of
output. `coverage.json` is one machine payload with the tree, drift, and
ranking sections. `report.md` is the same result for a human. One seed
per uncovered candidate sits at `drafts/<candidate>/proposal.md` with the
mined evidence inside. A rerun replaces the files the run owns and
leaves any other file in the run directory in place. Exit 0 on a
completed run and 2 on a failed fact call, with the reason on stderr.

## From a seed to a change

A seed is a scaffold, not a change. Pick one candidate with the user,
then start the normal `/opsx:propose` flow with the seed as the input.
The propose flow rewrites the scaffold, and the user approves the
proposal before any code. A seed text sits outside the STE hook, so the
first write of the text into `openspec/changes/` MUST pass the STE gate:
run the `pytest tests/spec_ste_check` gate, or rely on the spec-ste hook
in the primary checkout, before you push.
