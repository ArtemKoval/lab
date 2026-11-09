# Council Notes: proposal.md

## Author Summary

The author draft states the single-project resolution gap, the
worktree failure from issue 163, and the settled design: the
cross-project search for a named session, the `--project-dir` scope
rule, the newest-mtime selection, the exit-2 no-match, and the
unchanged default path. It scopes the delta to the requirement "The
CLI names the run sources" and lists the code, test, README, and
delta surfaces.

## Reviewer Challenges

- The Impact said the main spec changes in the implementation pull
  request. OpenSpec applies the delta at archive time.
- The exit-2 branch lives in `_run_build()`, not in
  `_resolve_transcript()`. The message today names a path, never the
  session.
- The cross-project search did not say "top-level files only". A
  recursive search could match a sidechain file under
  `<project>/<session>/subagents/`.
- Seven STE word breaches: slugifies, misses, hits, pins/pin, scans,
  substitutes, and the nouns tie-break and miss.
- The equal-mtime tie had no deterministic order.
- The `--transcript` precedence was only implied.
- The scope sentence omitted the README and the delta.
- "This lookup keeps its behavior" hid the removed fallback.
- The new helper needed the missing-directory guard.

## Resolutions

- Accepted: every finding. The final proposal fixes the archive-time
  statement, splits the exit-2 impact between
  `_resolve_transcript()` and `_run_build()`, narrows the search to
  top-level `.jsonl` files, replaces the unapproved words, pins the
  path-order tie, states the `--transcript` precedence, widens the
  scope sentence, spells out the removed fallback, and adds the
  helper guard note.
- Rejected: none.
- Deferred: the `sessions` subcommand keeps its worktree gap by
  declared scope. A future change can extend it.

## Remaining Risks

- Exit 2 is also the argparse usage-error code. The no-match message
  must name the session to stay distinguishable.
- The tie-break tests must use distinct modification times to avoid
  flaky ordering.
