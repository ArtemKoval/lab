# Tasks: add-loop-write-ledger

## 1. The tool

- [x] 1.1 Write `process_issues/ledger.py`: the store path from the
      lock state dir, the newline-guarded append, the read with the
      numbered skip notes, the pending view with the superseded flags,
      and the id generation over the injected clock and random source.
- [x] 1.2 Write the CLI wiring: the `ledger` command with the second
      positional action and the choices, the flag rules, the exit
      mapping, and the stderr notes.

## 2. Tests and docs

- [x] 2.1 Write `tests/process_issues/test_process_issues_ledger.py`:
      the append, the read skips, the pending dedup and superseded
      flags, the id freshness and collision regeneration, the three
      actions through the CLI, the failure set, and the missing-store
      cases.
- [x] 2.2 Extend the skill guard test with the Phases ledger order and
      the Failures pending presence.
- [x] 2.3 Update the skill (Commands, Phases with the numbered ledger
      sub-list, Failures), the README, and the delta scenario mapping.

## 3. Spec and delivery

- [x] 3.1 Carry the spec delta and pass the strict validate and the
      STE gate.
- [x] 3.2 Run the root suite, ruff, and the three gates on the changed
      paths.
- [x] 3.3 Commit, push, open the pull request, and merge after review.
