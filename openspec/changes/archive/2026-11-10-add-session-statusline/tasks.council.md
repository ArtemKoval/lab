# Council Notes: tasks.md

## Author Summary
The tasks cover the tool, the tests, the wiring with the doctor and
the registry, the docs, the CI gate lists, and the delivery gates.

## Reviewer Challenges
- The CI whitelist, coverage source list, and mutator paths had no
  task, and both lists sit under pin tests on a protected path.
- The registry test and the doctor run were unlisted.
- The unit order missed the shared venv dependency.

## Resolutions
- Accepted: the CI task 5.1 with the pin updates and the
  acknowledgment line on the pull request, the registry test task
  3.3, and the venv dependency note in 3.2.
- Rejected: none.
- Deferred: none.

## Remaining Risks
- The workflow edit pulls the protected-path acknowledgment onto the
  implementation pull request. The tasks carry it.
