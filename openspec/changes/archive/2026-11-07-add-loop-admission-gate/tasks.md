# Tasks: add-loop-admission-gate

## 1. The tool

- [x] 1.1 Write the pure admission predicate in `core.py`:
      `STATE_REFUSED`, `admitted(login, allowed)` over the login, the
      case-insensitive set, and the `[bot]` suffix, with a None login
      refusing.
- [x] 1.2 Write `authors.py`: the module-relative path constant, the
      load, and the shape validation, and `authors.json` with the
      operator login.
- [x] 1.3 Wire the CLI: the `author` field in both issue fetches, the
      `author` key in each queue entry, the config read between the
      lock and the first `gh` call with the exit-2 note, the refusal
      pre-check in the queue walk, and the status config row and the
      refusal in the blocked walk.

## 2. Tests and docs

- [x] 2.1 Write the admission cases: the refused state, the bot suffix,
      the case-insensitive list, the no-author case, the collision
      cases with the labels, and the argv pins on both fetches.
- [x] 2.2 Write the config cases: the shape validation, the empty-list
      refusal, the scan exit 2 with the path note, and the status
      config row with the level `config`.
- [x] 2.3 Write the regression case that proves the allowed path
      leaves every existing classification and the plain line format
      unchanged, and the status suppression case for the refused
      blocked issue.
- [x] 2.4 Update the README (the refused row, the config path, the
      exit-2 line, the status table) and the skill (States, the payload
      keys, the Scheduled run stop list, and the list edit path).

## 3. Spec and delivery

- [x] 3.1 Carry the spec delta and pass the strict validate and the
      STE gate.
- [x] 3.2 Run the root suite, ruff, and the three gates on the changed
      paths.
- [x] 3.3 Commit, push, open the pull request, and merge after review.
