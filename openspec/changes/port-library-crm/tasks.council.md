# Council Notes: tasks.md

## Author Summary

The task list was drafted by the primary agent during the z.ai peak window.
The reviewer findings and the builder check both shaped the revision.

## Reviewer Challenges

- Task 1.2 and 1.3 counted the crm-engine live spec in the hand-resolution
  set, which the exclusion removes. (CONFIRMED)
- The expected-set verification had no definition, and the report had no
  home. (CONFIRMED)
- The ADR port read as future work. (CONFIRMED)
- The task and design gate lists disagreed on prettier. (CONFIRMED)

## Resolutions

- Accepted: task 1.2 excludes `openspec/specs/` and verifies 154, 71, 6,
  and an empty deletion set. Task 1.3 resolves the 5 unions with the union
  order default, and task 1.4 owns compose.
- Accepted: task 1.1 writes the report to `reports/port_library_crm/` with
  a deletions row and carries unit tests for the script.
- Accepted: checked task 1.0 records the landed ADRs.
- Accepted: both lists name vitest, tsc, eslint, and prettier.
- Accepted builder defaults: ambient credentials with a stop on auth
  failure, scratch clones outside the repository, strict failure on any
  unexpected path or deletion, the merged README as the seed command source,
  stack detection with a recorded skip, the lab coverage floor with the
  child path entries, secret triage with a same-shape fake, and a stop with
  escalation on any archive-folder name collision.

## Builder Check Outcomes

- Answered in the artifacts: 24 questions, cited in the builder report.
- Theirs, resolved: the proposal pull request merges before implementation
  under the delegated merge authority of the full-delivery approval. The
  private child repository is fetchable under the active ArtemKoval
  account. The gate-integrity line lands at pull request creation for the
  one protected conftest path.

## Remaining Risks

- The mutation run wall clock stays unmeasured until it executes. The
  background plan absorbs it.
