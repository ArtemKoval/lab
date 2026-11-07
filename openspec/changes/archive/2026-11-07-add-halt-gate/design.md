# Design: add-halt-gate

## Plan review

The inner-loop review consulted the esf report, the peak-hours-gate spec, and
its hook contract test. The review settled these decisions:

- A separate hook script, not a condition inside the peak-hours gate. The two
  postures differ: the peak gate fails open on a broken environment, because
  it protects availability. The halt is a safety control, so it must deny
  when it can decide, even with a broken interpreter. One script cannot carry
  both postures cleanly.
- Pure bash plus one local git call. The deny path needs no venv, no module
  import, and no clock. The whole hook is two file tests, one bounded read,
  and one `git rev-parse`.
- The primary-root consultation: a worktree session resolves its own root, so
  the hook also consults the primary checkout through the git common dir. One
  halt file in the primary checkout stops the loops in every worktree, which
  is the core goal. The known limit: a symlinked segment in the hook path can
  derive a wrong root in the `$0` fallback, a limit the peak shim shares.
- The reason comes from the first line read within the first 200 bytes, with
  carriage returns removed, so a newline-less file cannot push unbounded
  bytes through the read and time the gate out. A file whose first line
  carries no readable text still denies, with a fallback reason.
- The halt file sits at `.claude/halt`. The gitignore carries it, because the
  file is runtime state and never a repository change.
- The matcher matches the peak-hours matcher. The halt targets model-backed
  work: dispatches, web access, and shell commands. A halt also denies the
  `gh issue create` call of a handover, so the operator opens the handover
  issue after the resume, or before the halt.
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
