# Tasks: add-loop-status-schedule

## 1. The tool

- [x] 1.1 Write `process_issues/status.py`: the pure `decide(facts)`
      table over the injected facts, the level names, and the exit
      codes.
- [x] 1.2 Write the CLI wiring: the `status` command in the parser,
      the fact gathering over the injected runners, the halt-file read
      at both locations, the auth and list probes, the blocked
      detection through `core.state_for_labels`, the lock verdict, and the
      plain and `--json` output.

## 2. Tests and docs

- [x] 2.1 Write `tests/process_issues/test_process_issues_status.py`:
      every table row, the precedence case, the unreadable case, the
      JSON shape, and the CLI paths with fake runners.
- [x] 2.2 Extend the skill guard test with the Scheduled run section:
      the recipe order rows and the per-level actions.
- [x] 2.3 Update the skill (Commands, Discipline, Pre-flight, and the
      Scheduled run section with the action table and the cron
      registration step), the README, and the
      proposal-PR body lines the recipe needs.

## 3. Spec and delivery

- [x] 3.1 Carry the spec delta and pass the strict validate and the
      STE gate.
- [x] 3.2 Run the root suite, ruff, and the three gates on the changed
      paths.
- [x] 3.3 Commit, push, open the pull request, and merge after review.
