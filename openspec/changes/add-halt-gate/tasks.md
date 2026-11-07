# Tasks: add-halt-gate

## 1. The hook

- [x] 1.1 Write `.claude/hooks/halt-gate.sh`: root resolution, the halt file
      test, the first-line reason cut at 200 characters, the deny message,
      and the exit contract.
- [x] 1.2 Add `.claude/halt` to the gitignore.

## 2. Wiring and tests

- [x] 2.1 Wire the PreToolUse group in `.claude/settings.json` through the
      update-config skill, with the peak-hours matcher and a timeout of 10.
- [x] 2.2 Write `tests/claude_infra/test_halt_gate_hook.py`: the executable
      bit, the wiring pins, and the live deny and allow paths.
- [x] 2.3 Add the CLAUDE.md hooks line.

## 3. Delivery

- [x] 3.1 Run the root suite and the STE gate.
- [ ] 3.2 Commit, push, open the pull request, and merge after review.
