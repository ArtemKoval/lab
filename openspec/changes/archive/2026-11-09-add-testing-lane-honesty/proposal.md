# Proposal: add-testing-lane-honesty

## Why

The lab gates e2e work behind environment variables, and a skipped e2e
mark is easy to read as coverage. Nothing states what a skipped lane
means, and nothing ties a lifecycle-risky change to the scenarios it
must cover. Proposal P4 of
`reports/2026-11-10-issue-175-rea-analysis.md` requests the rules. rea
states the rule that a skipped lane implies no coverage, and pairs
every lifecycle scenario with the assertions that prove it.

## What Changes

### The lane rule in Step 3

The testing step of the feature-pipeline skill gains one rule. A
skipped test lane implies no coverage, and the pull request body names
each lane the run skipped.

### The lifecycle rule in Step 9

The gates step gains one rule. A change to code with cleanup,
cancellation, or ownership behavior lists its lifecycle scenarios:
success, cleanup failure, cancellation mid-run, and partial
completion. Each scenario names the test that holds it.

## Capabilities

### New Capabilities

None. The rules live in the feature-pipeline skill, a harness surface
with no capability spec.

### Modified Capabilities

None. The change declares `skip_specs` and carries no delta.

## Out of scope

- No new test lanes and no lane registry. The existing marks and gates
  stay.
- No mechanical enforcement of the scenario table. The guard test pins
  the rule text, and the suite fails on a removal.
- No retrofit of existing tools. The rules bind new and touched code
  through the pipeline steps.

## Impact

- `.claude/skills/feature-pipeline/SKILL.md`: one rule bullet in
  Step 3 and one rule bullet in Step 9.
- `tests/claude_infra/test_pipeline_rules.py`: one guard test with one
  assertion per rule sentence.
- No code module, no registry unit, no README change, no spec delta.
