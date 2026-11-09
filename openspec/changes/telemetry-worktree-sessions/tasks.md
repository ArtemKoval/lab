# Tasks

## 1. Resolution helper

- [ ] 1.1 Add the cross-project search helper to
  `tools/handover_telemetry/handover_telemetry/transcript.py`: read
  the top-level `.jsonl` files of every project directory under
  `projects_root()`, skip missing directories, order by newest
  modification time with the path order as the tie-break, and return
  the first match for a named session stem.
- [ ] 1.2 Unit tests for the helper: a match in another project
  directory, the top-level rule against a sidechain file under
  `<project>/<session>/subagents/`, the newest-mtime selection with
  distinct mtimes, the path-order tie with equal mtimes, missing
  directories, and an absent `projects_root()`.

## 2. CLI resolution

- [ ] 2.1 Teach `_resolve_transcript()` the search and the scope:
  exact-slug lookup first, then the helper when no `--project-dir`
  is set, and the named directory as the only scope when it is.
- [ ] 2.2 Make `_run_build()` exit 2 and name the session when a
  named session has no match. Remove the newest fallback from the
  named-session path only.
- [ ] 2.3 Unit tests for the CLI paths: the cross-project build, the
  pinned `--project-dir` miss, the default path unchanged, and the
  no-match exit 2 message that names the session.

## 3. Docs and gates

- [ ] 3.1 Add the cross-project lookup line to
  `tools/handover_telemetry/README.md`.
- [ ] 3.2 Run the full hermetic suite, the CI coverage floor command,
  the CRAP gate, the dryer, and the mutation gate on the changed
  module. Nothing proceeds on red.
- [ ] 3.3 Run `openspec validate telemetry-worktree-sessions --type
  change --strict` and the Gate 0 lint before the implementation PR.
