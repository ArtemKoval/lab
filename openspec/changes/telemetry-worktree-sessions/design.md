# Design

## Decision summary

The grill-me round settled six decisions. Codebase facts settled the
first branch. The issue text and the session scope answers settled
the rest.

1. The default path keeps the newest-transcript behavior. The issue
   names `--session` only. The common case stays one directory read.
2. A named session with no `--project-dir` does the exact-slug lookup
   first, then searches the top-level `.jsonl` files of every project
   directory under `projects_root()`.
3. Several matches resolve to the newest file by modification time.
   Equal times order by path ascending, and the first wins.
4. `--project-dir` with `--session` sets the search scope to that one
   directory. No cross-project read happens, and the launch-path
   first lookup does not run.
4b. A session stem matches case-sensitively with no `.jsonl`
   normalization, as the exact-file lookup does today.
5. A named session with no match in scope fails the build with exit 2
   and a message that names the session. The silent newest fallback
   goes away for the named path. It produced the wrong-session block
   in the issue 163 run.
6. The `sessions` listing keeps its behavior. Extending it is a
   separate change.

## Flow

Container level, ASCII, lightweight C4-inspired. Assumption: one
transcript per session id at the top level of a project directory.
Open question: none at this level.

```
  build command flags                        disk under ~/.claude/projects/
  -------------------                        ------------------------------
  --transcript PATH  ---- wins, search does not run
                                                   |
  --session ID                                     v
       |                             +---------------------------+
       v                             | projects_root()           |
  +-----------------------------+    |  <slug-a>/<session>.jsonl |
  | _resolve_transcript()       |    |  <slug-b>/<session>.jsonl |
  | 1. --project-dir given?     |    |  <slug>/<session>/subagents/
  |    yes -> scope = that dir, |    +---------------------------+
  |    the launch-path lookup   |              ^
  |    does not run             |              | top-level .jsonl
  |    no  -> 2a. exact slug of |              | only, mtime desc,
  |        launch cwd first,    |              | path ascending on
  |        2b. then all dirs    |--------------+
  | 3. matches: newest mtime,   |
  |    path ascending on a tie  |
  | 4. none -> None, build      |
  |    exits 2, names session   |
  +-----------------------------+

  no --session, no --transcript
       |
       v
  newest_transcript(launch dir)   (unchanged)
```

Bullets:

- Boundary one: the resolution lives in the CLI layer. The parser,
  the redactor, and the renderer stay out of the change.
- The new helper in `transcript.py` reads directory names and
  top-level `.jsonl` files only. It skips project directories that do
  not exist and an absent `projects_root()`, as `newest_transcript()`
  does.
- The top-level rule keeps subagent files out of the search. A
  sidechain file under `<project>/<session>/subagents/` never wins
  the search.
- Exit 2 is also the usage-error code. The message names the session,
  so the operator can tell the failure modes apart.
- The `sessions` subcommand keeps the same worktree gap by declared
  scope. A future change can extend it.

## Alternatives

- A recursive search over each project directory: rejected. It can
  match a sidechain file whose stem equals the session id and resolve
  the wrong file.
- Keep the newest fallback on a miss: rejected. The silent fallback
  produced the wrong-session handover block in the issue 163 run.
- Extend the `sessions` listing to all projects: rejected for this
  change. It is a separate surface with no issue demand behind it.
- A configuration file for search roots: rejected. `projects_root()`
  already carries the roots, so the change adds no new component.
