## Why

The saturation report measured the harness and found the changed-paths
gate blind to the whole surface. A module outside a pull request diff
can rot while every pull request stays green. Proposal 2 of
`reports/2026-11-08-issue-123-saturation-testing-analysis.md` asks for
a scheduled saturation pass with a ratchet, and the operator approved
the run with a CLI and a scheduled workflow.

## What Changes

- Add `tools/saturation_pass`, a stdlib CLI that runs the vendored
  mutator over each owned Python tool with that tool's test suite.
- The CLI parses the printed per-function table of the mutator,
  aggregates it into per-module scores by the namespace column, and
  compares each module score against the committed store at
  `reports/saturation/scores.json`.
- A run refuses a drop. Exit 2 when any module score sits below the
  stored value. `--init` writes the first baseline without a
  comparison. `--update` writes the store after a clean run.
- Add `.github/workflows/saturation.yml`. A weekly cron pass and a
  `workflow_dispatch` pass with a tools input. The workflow enforces
  and never pushes to the store. The store moves only through pull
  requests.
- Wire `tools/saturation_pass` into the four CI gate lists, so the new
  tool sits under the same gates as the other owned tools.
- Carry a workflow timeout budget and a concurrency group.
- Record the placement decision in a new ADR that answers the ADR 0005
  rejection of whole-tree mutation on pull requests.
- Add a workflow contract test, a setup registry unit, a README, and a
  saturation-run skill.

## Capabilities

### New Capabilities

- `saturation-pass`: the saturation pass CLI, the score store, the
  ratchet, and the scheduled enforcement workflow.

### Modified Capabilities

- `quality-gates`: the CI gate path whitelist grows by
  `tools/saturation_pass`, and the requirement text drops the stale
  count of four owned tools. The per-pull-request resolution change is
  a separate change and stays out of this delta.

## Impact

- New tool at `tools/saturation_pass` with a module and a CLI.
  Standard library only.
- New store file at `reports/saturation/scores.json`, committed.
- New workflow at `.github/workflows/saturation.yml`, bounded by a
  timeout and outside the pull request path.
- New tests under `tests/saturation_pass/`. A workflow contract test
  in `tests/claude_infra/` pins the workflow file.
- One new unit in `tools/project_setup/registry.json`. The
  project-setup skill reads it.
- New skill at `.claude/skills/saturation-run/`. CLAUDE.md gains one
  project line.
- One new ADR file in `adr/` with the implementation pull request.
