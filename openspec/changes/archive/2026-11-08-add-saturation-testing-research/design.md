# Design: add-saturation-testing-research

## Context

The mutator mutates operators and constants, runs the tests once per mutant,
and prints a score of killed over killed plus survived. It exits 3 on a
survivor and exits 2 on a failed baseline. A site on a line the coverage
report misses counts as uncovered and does not run.

The quality gates run the mutator on changed paths only. CI derives the
paths from the pull request diff, caps the workers at 4, and resolves exit 3
at a score of 95 percent or more. The local pipeline rule is stricter: a
survivor on added or modified code dies before merge.

ADR 0005 accepted the three vendored tools as the default gates and rejected
whole-tree mutation per pull request, because its runtime is unbounded. This
research runs two bounded passes once and adds no gate, so that rejection
stays intact.

The host has 4 CPU cores and 15 GB of RAM. The anchor measurement runs about
96 mutants in about 2 minutes on `tools/process_issues`, which is about 48
mutants per minute at 4 workers. The root suite holds 100 percent line and
branch coverage on the owned tools, so uncovered sites stay rare.

The dsh analysis report at
`reports/2026-11-07-issue-103-dsh-superagent-analysis.md`
is the structure precedent. It landed as a `reports/` file with no change
directory and no spec delta.

## Goals / Non-Goals

**Goals:**

- Pin the saturation definition against the vendored mutator.
- Measure the saturation of two owned tools with full passes.
- Record per-module scores, the survivor map, and the cost minutes.
- Give adoption proposals in value order.

**Non-Goals:**

- Change no gate, no CI job, no tool, and no skill.
- Measure no tool beyond the two named ones.
- Implement no proposal from the report.

## Decisions

### D1. A docs-only change with `skip_specs`

The change writes a report and changes no behavior, so no capability delta
exists. The schema skips the specs artifact when `.openspec.yaml` declares
`skip_specs`. The dsh analysis landed the same way, as a `reports/` file.
Alternative: a minimal delta in the `quality-gates` capability. A delta would
state a report deliverable as a system requirement, and the archive would
freeze a report obligation into a behavior spec. That misuses the spec form,
so this design rejects it.

### D2. Two tools, not the repository

The passes cover `tools/process_issues` and `tools/spec_ste_check`.
process_issues is the loop engine and the anchor of the gate measurements.
spec_ste_check is a mid-size tool with the largest rules module. The report
names the remaining owned tools as follow-up work.
Alternative: a whole-repository pass now. Ten tools exceed any useful session
budget, and ADR 0005 keeps whole-tree runs out of CI. Two tools give a real
curve at bounded cost.

### D3. The CI command shape, widened

One coverage pass, then one mutator pass per tool:

```bash
tools/zai_routing_audit/.venv/bin/python -m coverage run \
  --data-file=target/coverage/python/.coverage \
  --source=tools/process_issues,tools/spec_ste_check,tests \
  -m pytest -q tests/process_issues tests/spec_ste_check
tools/zai_routing_audit/.venv/bin/python -m coverage lcov \
  --data-file=target/coverage/python/.coverage \
  -o target/coverage/python/lcov.info
tools/mutator/mutator --use-existing-coverage --max-workers 4 \
  --test-command "tools/zai_routing_audit/.venv/bin/python -m pytest -q tests/process_issues" \
  tools/process_issues
tools/mutator/mutator --use-existing-coverage --max-workers 4 \
  --test-command "tools/zai_routing_audit/.venv/bin/python -m pytest -q tests/spec_ste_check" \
  tools/spec_ste_check
```

- The commands reuse the CI gate shape and only widen the paths and scope the
  test command.
- The scoped test command keeps the per-mutant suite time near the anchor.
- The mutator runs the baseline once before the workers start. Exit 2 stops
  the pass.
Alternative: the default test discovery of the mutator. The owned tools carry
no in-tree venv, so discovery can pick the wrong interpreter. The explicit
command removes that guess.

### D4. Scan first, then budget

- `tools/mutator/mutator --scan tools/process_issues` lists the sites and
  runs no tests.
- The projection divides the site count by the anchor rate of about 48
  mutants per minute.
- The budget is 60 minutes per tool.
- A tool above the budget splits into per-module passes, and the report
  records minutes per module.
- The report records the projection and the actual side by side.
Alternative: one pass per module from the start. Modules are small, and each
per-module pass repeats the baseline, so the whole-tool pass with the
per-module fallback costs less.

### D5. The saturation score and its fields

- The score per module is killed divided by killed plus survived. This is the
  formula the mutator prints.
- A module is saturated when its survivor count is zero and its uncovered
  count is zero.
- The fields per module are: sites, uncovered, killed, survived, score in
  percent, and minutes.
- The survivor list carries the namespace, the form id, the line, and the
  mutation.
- The raw snapshots stay in `.metrics/mutate/`, and the report carries the
  summarized table.
Alternative: a second score with uncovered sites in the denominator. The
mutator prints the simple formula, and a second formula invites drift between
report and tool. The report keeps the tool formula and lists uncovered counts
beside it.

### D6. Provenance of the definition

The X post is login-walled. This run takes the definition from search
summaries of the post and from the 2016 mutation testing post at
blog.cleancoder.com. The report states this provenance in its scope section.
Alternative: skip the citation. The research names an external term, and a
wrong definition poisons the comparison, so the report cites what it could
read.

### D7. Proposals only, no adoption

The report lists proposals in value order, and each one becomes a separate
change. This change builds no gate and writes no threshold.
Alternative: adopt the ratchet in this change. The measurement lands first,
and a threshold without numbers is a guess.

## The report sections

1. Scope, with the provenance note of D6.
2. What saturation testing is, pinned against the mutator.
3. What the repository already covers.
4. The measurement, with the per-module table and the survivor list.
5. What a saturation practice adds: the whole-repo ratchet, the saturation
   curve per module, and the CI cost.
6. Proposals in value order.
7. Handover-style summary.

## Risks / Trade-offs

- The full pass takes more minutes than the projection. The scan pass
  projects the minutes first, and the 60-minute budget splits the pass per
  module.
- The anchor undercounts, because it measured only diff sites. The scan
  count is the real input to the projection, and the report records the
  actual minutes beside it.
- The baseline fails inside a worker tree. The mutator runs the baseline
  before the workers start and exits 2, and the report records the failure
  with the command.
- The two tools are a sample. The report states the sample and names the
  remaining tools as follow-up.
- Survivors in the two tools paint the loop engine weak. A survivor is a
  missing assertion, and the proposals order the fixes. The measurement is
  the point, not a verdict.
- The runs compete with other work for the 4 cores. One pass runs at a
  time, and `--max-workers 4` pins the cap to the core count.
- The X post stays unread. D6 records the provenance, and the report marks
  the definition as sourced from summaries.

## Migration Plan

- The proposal PR merges first, and the implementation branch lands the
  report after it.
- The report is additive, and a revert removes it with no other effect.
- The raw snapshots stay untracked, so the rollback needs no cleanup in git.

## Open Questions

- Which proposals the operator approves. That is the call of the user, and
  each approval opens a change.
- Where a saturation snapshot store would live. The ratchet proposal decides
  that with the numbers in hand.
- Whether the CI resolution at 95 percent should rise to exit 0. The report
  examines the gap, and a separate change owns the decision.
