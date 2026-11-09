# Tasks: add-confidence-discipline

## 1. The rule and the template

- [ ] 1.1 Add the confidence rules bullet to the working rules in
      `CLAUDE.md`, after the version-control bullet, with the three
      sentences.
- [ ] 1.2 Add the `## Limitations` and `## Open unknowns` sections to
      `.github/ISSUE_TEMPLATE/handover.md`, between Observations and
      Follow-ups.

## 2. Tests

- [ ] 2.1 Add `test_confidence_discipline_pinned` and
      `test_handover_template_has_the_unknown_sections` to
      `tests/claude_infra/test_working_rules.py`.

## 3. Spec and delivery

- [ ] 3.1 Carry the delta-less declaration and pass the strict
      validate and the STE gate.
- [ ] 3.2 Run the root suite and ruff on the changed test path.
- [ ] 3.3 Commit, push, open the pull request, and merge after review.
