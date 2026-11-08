# Tasks: add-saturation-testing-research

## 1. Proposal-phase checks

- [x] 1.1 Add the `skip_specs: true` line to `.openspec.yaml`, and confirm `openspec status --change add-saturation-testing-research --json` reports specs as skipped.
- [x] 1.2 Run `openspec validate add-saturation-testing-research --type change --strict`, and record the result.
- [x] 1.3 Run the STE checker over the change directory, and fix every error.
- [ ] 1.4 Merge the proposal PR, then cut the implementation branch from it in its own worktree.

## 2. Coverage input

- [ ] 2.1 Run the coverage pass from design D3, and confirm exit 0.
- [ ] 2.2 Convert the coverage data to LCOV at `target/coverage/python/lcov.info`.

## 3. Scan and budget

- [ ] 3.1 Run `tools/mutator/mutator --scan tools/process_issues`, and record the site count.
- [ ] 3.2 Run `tools/mutator/mutator --scan tools/spec_ste_check`, and record the site count.
- [ ] 3.3 Project the minutes per tool from the rate of about 48 mutants per minute, and compare with the 60-minute budget.

## 4. Mutation passes

- [ ] 4.1 Run the full pass on `tools/process_issues` with the D3 command, and capture the log.
- [ ] 4.2 Run the full pass on `tools/spec_ste_check` with the D3 command, and capture the log.
- [ ] 4.3 Split a pass per module when its projection exceeds the budget.
- [ ] 4.4 Record the exit code, the baseline result, and the wall-clock minutes per pass.

## 5. The report

- [ ] 5.1 Write `reports/2026-11-08-issue-123-saturation-testing-analysis.md` with the seven sections from the design.
- [ ] 5.2 Fill the per-module table: sites, uncovered, killed, survived, score in percent, and minutes.
- [ ] 5.3 List every survivor with its namespace, form id, line, and mutation.
- [ ] 5.4 Examine the whole-repo ratchet, the saturation curve per module, and the CI cost in section 5 of the report.
- [ ] 5.5 List the adoption proposals in value order in section 6 of the report.
- [ ] 5.6 Write the handover-style summary in section 7 of the report.

## 6. Gates and delivery

- [ ] 6.1 Run the root test suite with the shared venv, and confirm green.
- [ ] 6.2 Run the STE checker on the report path, and fix every error.
- [ ] 6.3 Confirm `.metrics/` and `target/` stay out of the commit.
- [ ] 6.4 Open the implementation PR with the proof line, and pass review.
- [ ] 6.5 After the merge, open the handover issue from the report summary, with the telemetry block.
