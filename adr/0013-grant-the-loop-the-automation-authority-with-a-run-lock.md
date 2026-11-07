# 0013 - Grant the process-issues loop the automation authority with a run lock

- Status: accepted, supersedes 0012
- Date: 2026-11-07

## Context

ADR 0012 grants the process-issues loop the automation authority. The
loop merges its own proposal and implementation pull requests, closes
issues, and runs the fix path without per-PR review. The two-label gate
is the only review control for spec-carrying changes, and the
`gh pr merge` allow set is part of the trust boundary. The same record
rejects a lock file for the single-run rule, because a stale lock wedges
the loop worse than the race it prevents. Proposal P1 of the dsh
analysis asks for that lock again, and the operator approved the build.
The rejection rested on the stale-lock wedge. The new design heals every
stale path that the rejection feared. The record carries the host, the
boot id, the process id, and the process start time, and the acquire
clears a stale lock. A foreign-host or hung holder heals through the 24
hour age rule or the force release. The revisit does not touch the
authority grant itself.

## Decision

The loop keeps the automation authority of ADR 0012. It merges its own
proposal and implementation pull requests to `main`, closes issues, and
runs the fix path without per-PR review. The two-label gate stays the
only review control for spec-carrying changes, and the allow set stays
part of the trust boundary. The single-run rule gains a mechanical
backstop. The loop takes the lock with `acquire --holder LABEL` before
the first scan and releases it at its end. The acquire command enforces
the lock with one exclusive file create. The scan examination is
cooperative. A stale lock never wedges the run. A record that does not
parse, an unknown schema version, a foreign boot id, a dead process id,
a start-time mismatch, or an age past 24 hours marks the lock stale, the
scan reports it and proceeds, and the acquire clears it and takes it.
The operator heals a lost or hung lock with `release --force`. Rejected
options: the edit of ADR 0012 in place, because history stays frozen. A
heartbeat, because a live but wedged holder is rare and the operator
path is enough. A 30 second age rule in the dsh manner, because this
lock spans a run of hours and a short age wedge new legitimate runs.

## Consequences

The in-force authority record moves from 0012 to this file, and 0012
stays as history. Two concurrent loop runs can no longer both scan and
work. The second acquire refuses with the holder details. The residual
risks stay: a live but wedged holder needs the operator, and the
stale-clear race lets two simultaneous acquirers of the same stale lock
proceed. The scan exemption is cooperative, so the lock defends against
an accidental double run, not against misuse.
