# Design: add-halt-gate

## Plan review

The inner-loop review consulted the esf report, the peak-hours-gate spec, and
its hook contract test. The review settled these decisions:

- A separate hook script, not a condition inside the peak-hours gate. The two
  postures differ: the peak gate fails open on a broken environment, because
  it protects availability. The halt is a safety control, so it must deny
  when it can decide, even with a broken interpreter. One script cannot carry
  both postures cleanly.
- Pure bash with no Python. The deny path needs no venv, no module import, and
  no clock. The whole hook is one file read and one test.
- The halt file sits at `.claude/halt`. The gitignore carries it, because the
  file is runtime state and never a repository change.
- The reason comes from the first line, cut at 200 characters. An unreadable
  or empty file still denies, with a fallback reason.
- The matcher matches the peak-hours matcher. The halt targets model-backed
  work: dispatches, web access, and shell commands.
- An unresolvable repository root exits 0, like the peak shim. The settings
  wiring always sets `CLAUDE_PROJECT_DIR`, so this path is a broken install,
  and the contract test pins the wiring that prevents it.

## ASIT pass

- Unification: the shim shape, the root resolution, and the wiring pattern
  come from the peak-hours gate hook. The contract test mirrors its test.
- Object removal: no CLI, no package, no venv, no status command. The file is
  the whole interface.
- No new dependency and no new component kind beyond one hook script.

## Spec delta

One new capability, `halt-gate`, with three requirements: the deny, the allow
paths, and the wiring and state.

## ADR review

No new ADR. The posture split between the two gates is a design decision the
design doc records. It changes no existing architecture record.
