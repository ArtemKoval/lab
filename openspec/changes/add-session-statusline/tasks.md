# Tasks: add-session-statusline

## 1. The tool

- [x] 1.1 Add `tools/session_statusline/session_statusline.py` with
      the payload-first render, the transcript sums with the running
      cache, the console fallback with the 300 second cache, the
      fail-open contract, `--json`, and the exit contract.
- [x] 1.2 Accept an injectable clock, transport, and cache path for
      the tests.

## 2. Tests

- [x] 2.1 Add `tests/session_statusline/` with the render, the
      fallbacks, the caches, and the fail-open cases, at 100 percent
      line and branch coverage.

## 3. The wiring

- [x] 3.1 Add the `statusLine` block to `.claude/settings.json` with
      the absolute-path command and `refreshInterval: 15`.
- [x] 3.2 Add the `session-statusline` unit to
      `tools/project_setup/registry.json` with the setup doctor at
      `tools/session_statusline_setup/session_statusline_setup.py`,
      and reflect the unit in the project-setup skill. The unit
      requires the shared zai venv unit first.
- [x] 3.3 Pin the registry unit test in `tests/session_statusline/`
      for the `session-statusline` unit, and run the doctor on the
      real repository.

## 4. Docs

- [x] 4.1 Add `tools/session_statusline/README.md`.
- [x] 4.2 Add one Projects line for the tool to `CLAUDE.md`.

## 4. Docs

- [x] 4.1 Add `tools/session_statusline/README.md`.
- [x] 4.2 Add one Projects line for the tool to `CLAUDE.md`.

## 5. The CI gates

- [x] 5.1 Extend the gate whitelist, the coverage source list, and the
      mutator product paths in `.github/workflows/tests.yml` with
      `tools/session_statusline` and `tools/session_statusline_setup`,
      and update the pins in
      `tests/claude_infra/test_ci_workflow.py`.

## 6. Spec and delivery

- [ ] 6.1 Pass the strict validate, the STE gate, the Gate 0 lint,
      the Gate 1 manifest proof, and the Gate 3 suites on the change.
- [x] 6.2 Run the root suite, ruff, and the three quality gates on
      the changed paths.
- [x] 6.3 Commit, push, open the implementation pull request with the
      `gate-integrity: acknowledged` line, and merge after review.
