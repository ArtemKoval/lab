# Design: add-loop-status-schedule

## Source

The requirement is proposal P2 of the dsh analysis. The grill round for
the six proposals settled one user-facing fork, the scheduler, and the
operator chose the Claude Code cron at 08:00 and 20:00 SGT. The
adversarial pair folded three blockers and six fixes into the
artifacts: the recipe keys on the level and the code, the recipe order
runs status first, the pipeline stop rules govern the issue work, the
auth probe is the local `gh auth token`, the unreadable-lock row is
exit 2 while a corrupt record stays stale, and status reuses the scan
classification for the blocked row.

## Plan review

- The recipe contradiction: an issue-list failure leaves no known
  actionable issues, so the recipe must branch on the level, not the
reviewer folded
  the raw code. The reviewer folded the level-keyed actions into the
  delta, and the proposal carries the action table.
- The auth command: `gh auth token` is local-only, so a network
  outage lands in the list row at exit 2, and exit 3 stays strictly
  missing setup. A revoked token that the probe accepts surfaces as a
  failed list call at exit 2.
- The peak window: status carries no window component. The window is a
  clock condition that ends without a halt, and a restart fixes
  neither exit 2 nor 3. The recipe runs the peak-hours-gate command,
  and the hook stays the backstop.
- The halt scope: status examines the halt file in both locations the
  halt-gate hook uses, the working root and the primary checkout
  root, because a session-root file must stop the report too.
- The blocked detection reuses the scan classification and its label
  precedence, so a handover+blocked issue never reports exit 2.
- Status calls gh before the lock, unlike the scan. The trade: a
  refused scan stays instant, while a healthy status consumes two
  read-only gh calls before the quiet exit 0. The stage-table
  principle decides: the operator-attention rows sit above the
  running rows.

## Diagrams

Format: ASCII in fenced blocks. Rigor: lightweight C4-inspired,
following the house precedent.

### Container diagram

```text
+-------------------------------------------------------------------+
| Claude Code cron session (the scheduled run)                      |
|                                                                   |
|  status --json --> action table --> peak check --> acquire        |
|       |                                  |             |          |
|       v                                  v             v          |
|  +-----------------+   +---------------------+   +-----------+    |
|  | status rows:    |   | peak-hours-gate     |   | acquire   |    |
|  | halt, auth,     |   | check (backstop)    |   | (lock)    |    |
|  | list, blocked,  |   +---------------------+   +-----------+    |
|  | lock            |                                              |
|  +--------+--------+                                              |
|           |  level + code                                         |
|           v                                                       |
|  action table: 0 quiet, 1 halt silent, 1 stale/idle proceed,      |
|  2 issue-list/lock stop, 2 blocked proceed+report, 3 stop         |
|           |                                                       |
|           v                                                       |
|  scan --> one issue through the pipeline phases --> release       |
+-------------------------------------------------------------------+
         |                            |                        |
         v                            v                        v
+----------------+   +----------------------------+   +------------+
| gh (auth, list)|   | .process_issues/lock.json  |   | .claude/   |
| (external)     |   | at the primary root        |   | halt       |
+----------------+   +----------------------------+   +------------+
```

### Component view inside the tool

```text
+----------------------------------------------------------------+
| tools/process_issues/process_issues/                           |
|                                                                |
|  status.py  pure decide(facts) -> (level, code, reason) over   |
|             injected facts; the CLI gathers the facts           |
|  cli.py     argparse: scan | acquire | release | status, the   |
|             status wiring over the runner seam                 |
|  lock.py    record I/O and the stale judgment (unchanged)      |
|  core.py    issue classification (reused for blocked)          |
+----------------------------------------------------------------+
```

## Decisions

1. The pure table `decide(facts)` takes the halt presence and reason,
   the auth result, the list result, the blocked entries, and the lock
   verdict, and returns the level, the code, and the reason. The CLI
   gathers the facts through the injected runners and the lock
   functions. Rationale: the table tests hermetically, and the IO
   stays at the CLI edge.
2. The auth probe is `gh auth token` with the argv ["auth", "token"]
   through the injected runner. A failed call or an empty token gives
   the setup row. The stdout is discarded. Rationale: the call is
   local-only, so a network outage lands in the list row at exit 2,
   and exit 3 stays strictly missing setup.
3. The halt rows examine both halt locations the halt-gate hook uses,
   the working root and the primary checkout root. The primary root
   resolves from the git common directory like the state dir.
   Rationale: a session-root halt file must stop the report too, and
   the hook contract names both locations.
4. The blocked detection reuses `core.classify` with its label
   precedence over the open-issue list. Rationale: a handover+blocked
   issue is skip in the scan, so status must not report it as blocked,
   and one classifier serves both commands.
5. The lock rows call `lock.read_record` and `lock.verdict` with
   holder=None and caller_pid=None. An OSError read gives exit 2, and
   a corrupt record falls in the stale row at exit 1. Rationale: the
   unreadable record is operator-attention, and the corrupt record
   heals on the next acquire.
6. Status calls gh before the lock. Rationale: the stage-table
   principle puts the operator-attention rows above the running rows,
   and the spec binds lock-before-gh to the scan only.
7. The recipe keys the action on the level and the code, not the bare
   code: exit 2 blocked proceeds, and exit 2 issue-list or lock stops.
   The issue work defers to the pipeline stop rules, so a fresh
   spec-carrying propose stops at the gate, and a propose-then-apply
   approval and the fix path continue under the pinned rules. Rationale:
   an issue-list failure leaves no known actionable issues, and the
   gate stop belongs to the pipeline, not to the recipe.
8. The cron registration lives in the harness with the schedule 08:00
   and 20:00 Singapore time, and the UTC fallback 00:00 and 12:00 when
   the cron takes no timezone field. Singapore sits at UTC+8 with no
   daylight saving, so the UTC fallback preserves the intent.
   Rationale: the repository cannot carry a harness cron, and the
   skill documents the one-time registration.
9. The guard test pins the skill recipe order with the same pattern as
   the P1 halt guard, and the Scheduled run heading is load-bearing.
   Rationale: one guard pattern serves both prose contracts.

## Decisions (continued)

10. The 200-issue list bound carries into status, and a blocked issue
    past the bound stays unreported. Rationale: one list call serves
    the blocked row and the issue-list row, and the scan carries the
    same bound.

## Failure modes

- Overlapping fires: a run that outlasts 12 hours holds a fresh lock,
  so the next fire reads exit 0 and quietly skips. A dead run ages
  into the stale rules or fails the pid probe, so the next fire
  proceeds and the acquire heals. A live race loses at the exclusive
  create. The lock answers the overlap.
- A revoked token that `gh auth token` still accepts surfaces as a
  failed list call at exit 2. The operator reads the reason.
- Cron liveness is unmonitored. A dead cron and a quiet healthy loop
  look identical. Accepted residual of the harness choice, and the
  operator can always run status by hand.
- A blocked issue past the 200-issue bound stays unreported. The scan
  carries the same bound.
- The quiet-skip invisibility: exit 0 and a healthy run print nothing
  in plain mode, so the operator gets no liveness signal across fires.
  Accepted in writing here. A digest is a later change.

## Builder settlements

The builder pass settled the remaining gaps. The JSON keys are
snake_case: `level`, `code`, `reason`, `blocked`, and `lock`, and the
stderr stays empty in `--json` mode. The level strings are `running`,
`halt`, `auth`, `issue-list`, `blocked`, `stale`, `idle`, and `lock`,
with `lock` for the unreadable row. When halt files exist at both
roots, the working-root file wins, in the manner of the hook
precedence. An empty first line in the halt file falls back to a fixed
reason. The plain-mode blocked line carries the issue numbers, and the
JSON entries carry the titles. An empty token is stdout that strips to
nothing. The no-lock row carries a lock summary with the state
`absent`, not null, because the examination reached the row. The cron
registers through the harness CronCreate tool, with the timezone field
when it exists and the UTC fallback otherwise. The registry declares
no governed capability here, so no bridge regen applies. The guard
test normalizes the double-THEN scenario to AND.

- Unification: status reuses the runner seam, the lock verdict, the
  core classifier, the state-dir resolution, and the skill guard
  pattern. No new component kind beyond one module.
- Division: the pure decide table sits in status.py, and the IO stays
  at the CLI edge.
- Breaking symmetry: the blocked row sits above the lock rows, and the
  auth row separates missing-setup from component-error at the trust
  boundary between 3 and 2.
- Object removal: no peak-window mathematics in status. The recipe
  runs the peak-hours-gate command. The halt rows reuse the two
  locations of the hook contract.
- No new dependency and no new component kind beyond one module in an
  existing package.
