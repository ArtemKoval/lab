# Tasks: add-loop-lock-check

## 1. The tool

- [x] 1.1 Write `process_issues/lock.py`: the record shape, the
      exclusive create, the clear, the release, the stale judgment over
      the injected liveness inputs, and the lock root resolution with
      the working-directory fallback.
- [x] 1.2 Write the CLI paths in `cli.py`: the `acquire` and `release`
      commands, the scan lock examination before the first `gh` call,
      the exit-64 usage rule, and the stderr contract.

## 2. Tests and docs

- [x] 2.1 Write `tests/process_issues/test_process_issues_lock.py`: the
      stale rules, the acquire and release paths, the scan refusal and
      the holder exemption, the exit-64 case, and the fake root
      resolver, all through injected inputs.
- [x] 2.2 Update `tools/process_issues/README.md`, the Discipline,
      Commands, and Pre-flight sections of the process-issues skill, and
      the `.gitignore` entry.

## 3. Spec and delivery

- [x] 3.1 Carry the spec delta and pass the strict validate and the STE
      gate.
- [x] 3.2 Run the root suite, ruff, and the three gates on the changed
      paths.
- [x] 3.3 Commit, push, open the pull request, and merge after review.
