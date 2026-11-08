# Proposal: add-saturation-testing-research

## Why

Issue 123 asks for research into saturation testing for the agentic harness
in this repository. Robert C. Martin defines saturation as the state with no
surviving mutant. His post names the crapper and mutator tools, and this
repository vendors both. The gates run the mutator on the changed paths of a
pull request. The gate never sees the rest of the harness surface, so the
saturation of the whole harness is unknown. ADR 0005 rejected whole-tree
mutation in CI, because its runtime is unbounded. A bounded measurement gives
the facts that an adoption decision needs.

## What Changes

### The report

- This change writes one analysis report at
  `reports/2026-11-08-issue-123-saturation-testing-analysis.md`.
- The report pins the saturation definition against the vendored mutator
  tool.
- The report follows the structure of
  `reports/2026-11-07-issue-103-dsh-superagent-analysis.md`.

### The measurement

- The run makes one full mutation pass over `tools/process_issues`.
- The run makes one full mutation pass over `tools/spec_ste_check`.
- Each pass runs on the product modules of one tool, with `--max-workers 4`
  and an explicit unit test command.
- One coverage pass gives the LCOV input, and `--use-existing-coverage` reads
  it.
- A scan pass counts the mutation sites before each full pass and projects
  the minutes.
- The budget is 60 minutes per tool, and a pass above the budget splits per
  module.
- The pass runs once. It is a measurement, not a new gate.

### The report fields

- The report records a saturation score per module, in the form killed
  divided by killed plus survived.
- The report records the survivor list with the namespace, the form id, the
  line, and the mutation.
- The report records the uncovered count and the cost minutes per pass.
- The report examines a whole-repo ratchet, a saturation curve per module,
  and the CI cost of a wider practice.
- The report lists adoption proposals in value order. Each proposal becomes
  its own change with its own review.

### No code change

- This change adds no tool, no gate, no CI job, and no skill text.
- The registry gains no unit.

## Capabilities

### New Capabilities

None. This change writes a report and changes no behavior.

### Modified Capabilities

None. No spec-level behavior changes. The change declares `skip_specs` in
`.openspec.yaml`, so the specs artifact reads skipped and carries no delta
file. The analysis-only precedent is the dsh report, which landed as a
`reports/` file with no capability delta.

## Out of scope

- No mutation pass beyond the two named tools. The other owned tools are
  follow-up proposals in the report.
- No whole-repo pass and no new CI job. ADR 0005 keeps whole-tree mutation
  out of pull requests.
- No adoption work. Each proposal becomes a separate change.
- No `gates.yaml` and no `rubrics/`. No governed capability changes.
- No spec delta. The `skip_specs` declaration carries it.
- No change to any gate threshold. The report examines thresholds only.

## Impact

- `reports/2026-11-08-issue-123-saturation-testing-analysis.md` (new): the
  full artifact of this change.
- `openspec/changes/add-saturation-testing-research/.openspec.yaml`: gains
  the `skip_specs` line.
- The handover issue after the merge, with the telemetry block (Step 13).
- `.metrics/` and `target/` hold the raw mutation snapshots, and the ignore
  rules exclude both from git.
- No code, no tests, no CI, and no registry change.
