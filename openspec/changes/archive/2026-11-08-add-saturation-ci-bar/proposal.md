## Why

The CI mutation gate resolves the mutator's exit 3 against a 95
percent score floor, so a pull request with surviving mutants can
pass when the score stays high. The operator approved proposal 3 of
`reports/2026-11-08-issue-123-saturation-testing-analysis.md`: the
changed-paths gate rises to the saturation bar. CLAUDE.md already
holds new code to mutation with no survivors, so the resolution is
the last soft spot, and the one known survivor died in the first
change of this run.

## What Changes

- The CI mutator step in `.github/workflows/tests.yml` drops the
  exit-3 score resolution. Any non-zero mutator exit fails the pull
  request: exit 3 for a survivor, exit 2 for a failed baseline.
- The workflow contract test pin changes with the workflow: the
  resolution assertion leaves, and the direct invocation stays.
- The `quality-gates` spec gains the saturation bar as a formal
  requirement, and its Purpose sentence names the bar instead of the
  95 percent resolution.
- The feature-pipeline skill's gate line names the saturation bar
  instead of the score floor.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `quality-gates`: the CI mutation bar becomes exit 0 on the changed
  paths, with no score resolution, and the Purpose sentence moves
  from the 95 percent floor to the saturation bar.

## Impact

- `.github/workflows/tests.yml`, a protected path, so the
  implementation pull request carries the
  `gate-integrity: acknowledged` line and the merge is the
  acknowledgment.
- `tests/claude_infra/test_ci_workflow.py`, the contract pin.
- `openspec/specs/quality-gates/spec.md` Purpose sentence, edited in
  the implementation pull request beside the delta.
- `.claude/skills/feature-pipeline/SKILL.md`, one gate line.
- Current surfaces stay green: the loop engine holds exit 0 on its
  full pass, and the checker joined it in this run.
