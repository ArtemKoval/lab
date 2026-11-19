## 1. Port execution

- [ ] 1.1 Write the port script at `tools/port_library_crm/`: fetch the child
  head `210247d`, compute `git merge-tree --write-tree` with base `05c3ddd`,
  apply the merged files to the branch, stage the conflict list, and print
  the file-count report.
- [ ] 1.2 Run the port script. Verify the counts: 154 copied files, 71
  transferred files, 7 conflicts, and no file outside the expected set.
- [ ] 1.3 Resolve the 6 union conflicts: `CLAUDE.md`, `.coveragerc`,
  `.gitignore`, `crm/README.md`, the `crm-local-aws` skill, and the
  `crm-engine` spec.
- [ ] 1.4 Resolve `crm/deploy/compose.yaml`: keep the Langfuse profile and
  the loopback database, add `crm/deploy/compose.demo.yaml`, and point
  `demo_up.sh` at both compose files.
- [ ] 1.5 Remove the skip set from the merged tree: the stale
  `add-sec-scan` change, `.claude/tests/`, and the scratch files `W`, `W3`,
  and the two concat files under `tests/slidecast/`.
- [ ] 1.6 Run the STE gate over every ported file under `openspec/`. Fix any
  drift the gate reports.

## 2. Integration proof on the merged tree

- [ ] 2.1 Run the crm Python suite from `crm/` and make it green.
- [ ] 2.2 Run the dashboard gates: vitest, tsc, eslint, and prettier, and
  make them green.
- [ ] 2.3 Run the library pack gates outside the browser: the pack
  validator, the seed into a scratch database, and the pack smoke run.
- [ ] 2.4 Run the library e2e flow when the host carries the stack, and
  record the lane as skipped in the pull request body otherwise.
- [ ] 2.5 Run the root suite with the slidecast tests and make it green.
- [ ] 2.6 Run the coverage gate with branch coverage. Hold 100 percent line
  and branch coverage of the ported code, and ratchet the configured floor.
- [ ] 2.7 Run the complexity gate over every ported Python function. Hold 10
  or less, and split any function above 10 in this change.
- [ ] 2.8 Run crapper and dryer over the ported Python surface. Hold CRAP at
  10 or less and no duplication pair at or above 0.8.
- [ ] 2.9 Run the mutator over every ported Python module in an out-of-tree
  copy, in the background, and drive every survivor to death with a test.
- [ ] 2.10 Run `sec-scan --diff` over the branch diff, with the child
  literals checked against the scan.
- [ ] 2.11 Examine the saturation pass scope for the slidecast modules, and
  initialize the baseline through the `saturation-run` skill when they fall
  in scope.

## 3. Docs and harness sync

- [ ] 3.1 Verify the merged `README.md` and `CLAUDE.md` against the tree:
  every command runs, and every path exists.
- [ ] 3.2 Verify the `crm-app` and `crm-local-aws` skill text against the
  merged files, and fix any drift.
- [ ] 3.3 Verify the project-setup completeness test passes with no new
  unit, and record the registry verdict in the pull request body.

## 4. Review and merge

- [ ] 4.1 Run the adversarial review over the whole diff after the peak
  window closes, verify each finding against the code, and fix every
  confirmed finding.
- [ ] 4.2 Re-run the suite and the gates after the fixes, including the
  former survivors.
- [ ] 4.3 Open the implementation pull request with the summary, the
  mechanism, the test plan with observed results, the skipped lanes, and the
  attribution line.
- [ ] 4.4 Merge by squash, delete the branch, resync `main`, and run the
  residue scan.
- [ ] 4.5 Run `openspec validate port-library-crm --type change --strict`,
  archive the change on its own branch, and merge the archive pull request.
- [ ] 4.6 Open the handover issue with the handover-telemetry block and the
  port provenance range `05c3ddd..210247d`.
