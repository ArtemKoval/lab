## 1. Port execution

- [x] 1.0 Port the two child ADRs as 0018 and 0019. Landed with the
  proposal branch.
- [x] 1.1 Write the port script at `tools/port_library_crm/` with unit
  tests: fetch the child head `210247d`, compute `git merge-tree
  --write-tree` with base `05c3ddd`, apply the merged files to the branch,
  stage the conflict list, and write the report with a deletions row to
  `reports/port_library_crm/`.
- [x] 1.2 Run the port script with `openspec/specs/` excluded from the
  applied set. Verify the counts the report records: 151 copied files, 76
  transferred files, 6 conflicts, an empty deletion set, and no path
  outside the expected set, which reconciles to the child's 154 additions
  and 78 modifications once the five excluded spec paths join. Stop on any
  unexpected path or deletion.
- [x] 1.3 Resolve the 5 union conflicts: `CLAUDE.md`, `.coveragerc`,
  `.gitignore`, `crm/README.md`, and the `crm-local-aws` skill. The sixth
  conflict, the `crm-engine` live spec, stays unapplied through the
  exclusion. Union order: the lab lines first, the child lines appended,
  exact duplicate lines deduplicated.
- [x] 1.4 Resolve `crm/deploy/compose.yaml`: keep the Langfuse services,
  add the demo `db` service bound to `127.0.0.1:5433`, add
  `crm/deploy/compose.demo.yaml` with the public binding, point
  `demo_up.sh` at both compose files, and pin the contract in the compose
  test.
- [x] 1.5 Remove the skip set from the merged tree: the stale
  `add-sec-scan` change, `.claude/tests/`, and the scratch files `W`, `W3`,
  and the two concat files under `tests/slidecast/`.
- [x] 1.6 Run the STE gate over every ported file under `openspec/`. Fix any
  drift the gate reports.

## 2. Integration proof on the merged tree

- [x] 2.1 Run the crm Python suite from `crm/` and make it green. Adjust
  the desk and resolution fixtures in `crm/conftest.py` if the suite names
  them.
- [x] 2.2 Run the dashboard gates: vitest, tsc, eslint, and prettier, and
  make them green.
- [x] 2.3 Run the library pack gates outside the browser: the pack
  validator, the seed into a scratch database, and the pack smoke run.
- [x] 2.4 Run the library e2e flow when the host carries the stack, and
  record the lane as skipped in the pull request body otherwise.
- [x] 2.5 Run the root suite with the slidecast tests and make it green.
- [x] 2.6 Run the coverage gate with branch coverage. Hold 100 percent line
  and branch coverage of the ported Python, keep the lab `fail_under`
  floor, and add the child path entries to `.coveragerc`.
- [x] 2.7 Run the complexity gate over every ported Python function. Hold 10
  or less, and split any function above 10 in this change.
- [x] 2.8 Run crapper and dryer over the ported Python surface. Hold CRAP at
  10 or less and no duplication pair at or above 0.8.
- [x] 2.9 Run the mutator over every ported Python module in an out-of-tree
  copy that mirrors the repository layout, because the slidecast conftest
  switches its import root on `MUTANT_UNDER_TEST`. Drive every survivor to
  death with a test.
- [x] 2.10 Run `sec-scan --diff` over the branch diff, and triage every
  finding. A real child secret becomes a same-shape fake, and the pull
  request records the one verbatim break.
- [x] 2.11 Examine the saturation pass scope for the slidecast modules, and
  initialize the baseline through the `saturation-run` skill when they fall
  in scope.

## 3. Docs and harness sync

- [x] 3.1 Verify the merged `README.md` and `CLAUDE.md` against the tree:
  every command runs, and every path exists.
- [x] 3.2 Verify the `crm-app` and `crm-local-aws` skill text against the
  merged files, and fix any drift.
- [x] 3.3 Verify the project-setup completeness test passes with no new
  unit, and record the registry verdict in the pull request body.

## 4. Review and merge

- [x] 4.1 Run the adversarial review over the whole diff, verify each
  finding against the code, and fix every confirmed finding.
- [x] 4.2 Re-run the suite and the gates after the fixes, including the
  former survivors.
- [x] 4.3 Open the implementation pull request with the summary, the
  mechanism, the test plan with observed results, the skipped lanes, the
  `gate-integrity: acknowledged` line for the two protected conftest paths
  (`tests/slidecast/conftest.py` and `tests/port_library_crm/conftest.py`,
  both additions), and the attribution line.
- [x] 4.4 Merge by squash, delete the branch, resync `main`, and run the
  residue scan.
- [x] 4.5 Run `openspec validate port-library-crm --type change --strict`,
  archive the change on its own branch, and merge the archive pull request.
  The archive applies the deltas to the live specs.
- [ ] 4.6 Open the handover issue with the handover-telemetry block and the
  port provenance range `05c3ddd..210247d`.
