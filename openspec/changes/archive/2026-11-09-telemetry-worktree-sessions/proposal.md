## Why

The build resolves its transcript inside one project directory.
`project_dir_for()` makes the project directory name from the launch
path. `_resolve_transcript()` searches only that directory under
`projects_root()`.

When a run starts in a worktree, Claude Code writes the session
transcript under the project directory of the worktree path. The
build does not find the named `--session` when the transcript is in
another project directory. The build then silently uses the newest
transcript of the wrong project. The issue 163 run got the previous
session as its source. Its handover block described the wrong
session.

The worktree rule gives each feature run its own worktree. Each of
those runs has this problem in its handover build. The current
workaround builds the block from the `.cc_logging` log alone.

Issue 163, follow-up 4 asks: "Teach handover-telemetry to reach
session transcripts that live in worktree project directories, and
honor `--session` there."

## What Changes

- The `build` command gains a cross-project search for a named
  session.
- With `--session` and no `--project-dir`, the build first resolves
  `<session>.jsonl` in the project directory of the launch path. The
  build keeps this first lookup, and no newest-file fallback follows
  it.
- When that file is absent, the build searches the top-level
  `.jsonl` files of every project directory under `projects_root()`.
- When several project directories hold a match, the build uses the
  newest file by modification time. The path order breaks a tie.
- With `--session` and `--project-dir`, the named directory sets the
  search scope. The build resolves the session only in that
  directory. It does not read other project directories.
- `--transcript` still wins, and the search does not run.
- The build fails with exit 2 when a named session has no match in
  the search scope. The failure message names the session.
- The named-session path no longer uses the newest transcript.
- The default source stays the newest transcript of the launch
  project. The build keeps this behavior with no `--session` and no
  `--transcript`.
- The hook log keeps its resolution from `--repo`. The subagent
  files keep their resolution beside the transcript.
- The `sessions` subcommand keeps its behavior. It is out of scope.
- The delta spec modifies the requirement "The CLI names the run
  sources". The default-source scenario keeps its text. The delta
  adds scenarios for the cross-project match, the search scope, the
  newest-file selection, and the no-match failure.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `handover-telemetry`: The requirement "The CLI names the run
  sources" changes. The named `--session` resolves across the
  project directories under `projects_root()` when the launch
  project directory does not hold it. The named directory sets the
  search scope when the command carries `--project-dir`. A named
  session with no match exits with code 2. The build does not
  silently use the newest transcript. The default-source scenario
  keeps its text.

## Impact

- `tools/handover_telemetry/handover_telemetry/cli.py`:
  `_resolve_transcript()` gains the search and the scoped no-match
  result. `_run_build()` exits 2 on the no-match with a message that
  names the session. `_resolve_project_dir()` keeps its behavior.
- `tools/handover_telemetry/handover_telemetry/transcript.py`: one
  new helper searches the top-level `.jsonl` files of the project
  directories under `projects_root()`. The helper skips project
  directories that do not exist and handles an absent
  `projects_root()`. `projects_root()`, `project_dir_for()`,
  `newest_transcript()`, and `sidechain_files()` keep their
  behavior.
- `tests/handover_telemetry/`: new tests for the cross-project
  match, the search scope, the newest-file selection, and the
  no-match failure. The tie-break tests use distinct modification
  times. The default-path tests stay green.
- The delta at
  `openspec/changes/telemetry-worktree-sessions/specs/handover-telemetry/spec.md`.
  The main spec keeps its text until the archive step applies the
  delta. The delta text passes the `tools/spec_ste_check` gate.
- `tools/handover_telemetry/README.md`: one usage line on the
  cross-project lookup.
- Scope: the change stays repo-local to `tools/handover_telemetry`,
  its tests, the tool README, and the change delta. The change adds
  no dependency. The transcript files keep their format. The hook,
  the redaction, and the parser keep their behavior.
