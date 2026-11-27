# Proposal: add-spec-mining-seeds

## Why

The spec-mining run of 2026-11-09 found six uncovered candidates and
wrote six seed scaffolds at `reports/spec_mining/2026-11-09/drafts/`.
Issue 265 orders the conversion: run the seed-to-propose flow per
seed. The seeds are bare scaffolds, so this proposal derives every
requirement from the real surface behavior, verified against the
tree on 2026-11-27. Confidence: observed. The surfaces are the
`apple/fm/simple_game` build, `tools/knights_notebook_run`, the
`notebooks/` tests, `tools/project_setup`, and `tools/spec_mining`.

## What Changes

- The `apple-fm` capability pins the simple_game build contract: the
  step ledger, the model-driven steps, the gates with one repair
  pass, the frozen contracts, and the local-only rule.
- The `knights-notebook-run` capability pins the runner contract: the
  executed copy beside a clean source, the environment shim with its
  guidance, and the package installs.
- The `notebooks` capability pins the notebook tests: hermetic and
  standard-library shaped, with the public checklist (cleared
  outputs, no secrets, the allowed non-ASCII set).
- The `project-setup` capability pins the registry shape, the venv
  units, the interview protocol, the doctor contract, and the
  backup-and-verify installer.
- The `spec-mining` capability pins the mining tool: the dated report
  directory, the tree scan, the drift scan, the history ranking, and
  the exit codes.
- The `configs/wezterm` seed converts as a recorded skip: no suite
  exercises the config and no scenario is testable today. The
  proposal records the skip per seed, and the issue comment repeats
  it.

## Capabilities

### New Capabilities

- `apple-fm`, `knights-notebook-run`, `notebooks`, `project-setup`,
  and `spec-mining`, one new capability per seed, with the
  requirements above.

### Modified Capabilities

None.

## Impact

- `openspec/specs/` gains five new capability directories through the
  archive sync of this change.
- No production code changes: the change is spec-only, so the apply
  phase carries no implementation tasks and the enforcing coverage is
  the existing suites that already pin these surfaces
  (`tests/notebooks/`, the setup completeness test, the spec-mining
  suite).
- `openspec/eval_manifest.json` changes through the bridge regen.
- The diff touches no protected gate path, so the pull request needs
  no `gate-integrity: acknowledged` line.
- The skill's flow names one candidate per propose, picked with the
  user. Issue 265 aggregates the six seeds, and the loop carries one
  change per issue, so this change reviews the five conversions and
  the one skip as one unit. The gate can drop any capability delta at
  review: the fold removes one delta file, and the other four stand.
