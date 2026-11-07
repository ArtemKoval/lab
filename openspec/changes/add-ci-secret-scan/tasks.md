# Tasks: add-ci-secret-scan

## 1. The diff mode

- [ ] 1.1 Add the diff parser: file headers, hunk ranges, new-file line
      numbers, added lines only, and the deletion and no-newline cases.
- [ ] 1.2 Add `scan_diff` over the parsed lines with the existing rule set.
- [ ] 1.3 Add `--diff REF` to the CLI, the `SECRET_SCAN_LITERALS` reading,
      and the hash-prefix literal findings.

## 2. Tests

- [ ] 2.1 Unit tests for the parser, the diff scan, the literal rule, and
      the exit codes, with a fake runner.
- [ ] 2.2 Write `tests/claude_infra/test_secret_scan_workflow.py` to pin the
      workflow file.

## 3. Delivery

- [ ] 3.1 Run the root suite, ruff on the tool, and the three gates on the
      changed paths.
- [ ] 3.2 Commit, push, open the pull request, and merge after review.
