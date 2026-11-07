# Council Notes: proposal.md

## Author Summary

The author agent revised the draft around six settled decisions: the lock
file at the primary checkout root resolved from the git common directory,
the holder label flag as the only portable owner identity across one
process per CLI call, liveness-based staleness with a start-time match,
the read-only scan with the clear-and-take in acquire, the skill-owned
halt step, and the exit-64 usage rule that keeps exit 2 in one category.

## Reviewer Challenges

- BLOCKER: the draft said "repository root", which licenses a cwd-rooted
  lock and misses the two-worktree collision this change targets.
- BLOCKER: the draft was silent on ADR 0012, which rejects a lock file in
  its accepted Decision. A superseding ADR must restate the whole grant
  because the in-force set walks Supersedes links.
- BLOCKER: a foreign-host lock never heals under pure liveness, which
  returns the wedge ADR 0012 feared.
- BLOCKER: a crash between the exclusive create and the write leaves a
  corrupt file that wedges every later scan at exit 2.
- BLOCKER: a static holder label lets two runs from the same skill share
  the exemption, so the lock does nothing for its target scenario.
- SHOULD-FIX: missing edge contract for acquire and release, exit 64
  absent from the proposal text, `core.py` charter conflicts with lock
  I/O, README and skill Commands sections missing from Impact, no Out of
  scope section, halt file location and pre-flight order unstated, and a
  reboot pid edge that a boot id field closes at zero cost.

## Resolutions

- Accepted: primary checkout root wording, the git common directory
  resolution with the working-directory fallback, and the injected root
  resolver test.
- Accepted: the ADR acknowledgment in Why, the superseding ADR in Impact,
  and the restated automation authority in the new ADR.
- Accepted: the 24 hour age rule that heals a foreign-host or rebooted
  lock, and `lock release --force` as the operator escape.
- Accepted: the corrupt-record-is-stale rule and the single-write record
  after the exclusive create.
- Accepted: a unique holder label per run, with the honest enforcement
  split: acquire enforces, the scan exemption is cooperative.
- Accepted: the exit-64 remap, the edge contract sentences, the new
  `lock.py` module, the README and skill Commands impact lines, the Out
  of scope section, and the halt location and pre-flight order.
- Rejected: surface tags on the delta scenarios. The schema routes
  scenarios to the dspy bridge for governed capabilities, and every
  existing spec in this repository carries no tags, because
  process-issues is not in the harness registry.
- Rejected: a 30 second stale age in the dsh manner. dsh holds its lock
  around store access, while this lock spans a run of hours.

## Remaining Risks

- A live but wedged holder never auto-heals. The operator uses the halt
  file, kills the holder, and releases with `--force`.
- The stale-clear race lets two simultaneous acquirers of the same stale
  lock both proceed. Both already saw no live holder.
- `--path-format=absolute` needs git 2.31 or newer. The fake resolver
  test carries the primary path, and the working-directory fallback
  covers an old git.
