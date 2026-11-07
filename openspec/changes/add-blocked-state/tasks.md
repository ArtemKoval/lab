# Tasks: add-blocked-state

## 1. The scanner

- [ ] 1.1 Carry the `blocked` label and state in the core classification,
      in a table-driven precedence between `handover` and `answered`.

## 2. Tests and docs

- [ ] 2.1 Extend `tests/process_issues/`: the blocked classification, the
      precedence cases, and one scan JSON case.
- [ ] 2.2 Add the rule to the process-issues skill, and move its stale spec
      path.
- [ ] 2.3 Update the README state table and the precedence line.

## 3. Spec and delivery

- [ ] 3.1 Carry the spec delta and pass the strict validate, the lint, and
      the bridge regen.
- [ ] 3.2 Run the root suite and the STE gate.
- [ ] 3.3 Commit, push, open the pull request, and merge after review.
