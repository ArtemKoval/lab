## 1. Scenario-to-test map

- [ ] 1.1 Map every delta scenario to its enforcing test. Record the
      map in the pull request body.
- [ ] 1.2 Add the missing tests in
      `tests/negative_instruction_audit/`: absent `CLAUDE.md` drop,
      output-styles out, charter-last order, the five miss-class
      shapes, whitespace collapse on both pin sides, the
      candidate-inside-pin direction, an unpinned candidate in the
      record and the payload, the five totals counts, the JSON
      `root` key, a silent file with no output line, the 110-character
      cut, the read-only tree invariance, and the default root.

## 2. Gates

- [ ] 2.1 Run the full hermetic suite with the shared venv
      interpreter (`tools/zai_routing_audit/.venv/bin/python -m
      pytest` from the main checkout when a worktree lacks the venv)
      and hold it green.
- [ ] 2.2 Run `openspec validate
      add-negative-instruction-audit-spec --type change --strict`
      before the archive step.
- [ ] 2.3 Run `tools/spec_ste_check` on the change text and hold it
      clean.

## 3. Docs

- [ ] 3.1 Tick each task in this file as the work lands.
- [ ] 3.2 Confirm the README and the CLAUDE.md Projects line stay
      accurate, and change nothing when they do.
