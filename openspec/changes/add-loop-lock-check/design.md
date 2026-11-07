# Design: add-loop-lock-check

## Source

The requirement is proposal P1 of
`reports/2026-11-07-issue-103-dsh-superagent-analysis.md`, which the user
approved as part of "implement all proposals from p1 to p6". The grill
round for the six proposals settled one user-facing fork, the P2
scheduler, and the user chose Claude Code cron at 08:00 and 20:00 SGT.
No user-facing fork exists in this change. The adversarial pair folded
five blocker findings and eight fix findings into the artifacts.

## Plan review

- A cwd-rooted lock misses the two-worktree collision, the real
  concurrency case under the house worktree discipline. The lock root
  resolves from `git rev-parse --path-format=absolute --git-common-dir`
  and falls back to the working directory.
- ADR 0012 rejected a lock file because a stale lock wedges the loop.
  The answer has three parts: the stale rules are liveness-based, the
  acquire clears a stale lock, and `release --force` plus the 24
  hour age rule heal a foreign-host, rebooted, or hung holder. The
  superseding ADR restates the whole 0012 grant, because the schema
  derives the in-force set by walking Supersedes links.
- A crash between the exclusive create and the write leaves a corrupt
  record. A corrupt record is stale by definition, so the loop heals.
- A static holder label lets two runs share the exemption. The skill
  builds the label per run from the date and four hex characters.
- Argparse exits 2 on a usage error, which collides with the exit-2
  contract. The CLI maps a usage error to exit 64.
- The scan stays read-only. The report and the destructive action stay
  separate, in the residue-scan manner.

## Diagrams

Format: ASCII in fenced blocks. Rigor: lightweight C4-inspired. Both
choices follow the add-peak-hours-gate precedent.

### Container diagram

```text
+-------------------------------------------------------------------+
| Claude Code session (the loop run)                                |
|                                                                   |
|  pre-flight: halt file --> peak window --> acquire               |
|                                          |                        |
|                                          v                        |
|              +----------------------------------------+           |
|              | tools/process_issues CLI               |           |
|              | scan | acquire | release | --force      |           |
|              +----+-----------------------+-----------+           |
|                   |                       |                       |
|      lock examine before first gh         |                       |
|                   v                       v                       |
|     +------------------------+   +--------------------------+     |
|     | .process_issues/       |   | gh (GitHub CLI)          |     |
|     | lock.json at the       |   | issue list, pr list      |     |
|     | primary checkout root  |   +--------------------------+     |
|     +------------------------+                                    |
+-------------------------------------------------------------------+
         |                                       |
         v                                       v
+---------------------+              +------------------------+
| the second session  |              | GitHub (issues, PRs)   |
| sees exit 2 and the |              | (external)             |
| holder details      |              +------------------------+
+---------------------+
```

### Component view inside the tool

```text
+----------------------------------------------------------------+
| tools/process_issues/process_issues/                           |
|                                                                |
|  lock.py    record shape, exclusive create, clear, release,    |
|             stale judgment over injected liveness inputs       |
|  cli.py     argparse: scan | acquire | release, --holder,      |
|             --force, exit 64 usage rule, lock root resolve     |
|  core.py    pure issue classification, unchanged               |
|  __main__.py the module entry                                  |
+----------------------------------------------------------------+
```

## Decisions

1. The lock root resolves from `git rev-parse --path-format=absolute
   --git-common-dir`. The state dir is the common dir parent plus
   `.process_issues`. The resolver is injectable, and a failed or old-git
   call falls back to the working directory. Rationale: the primary
   checkout root guards the two-worktree collision, and the fallback
   keeps the tests and a non-git root working.
2. `lock.py` carries the I/O and the judgment seam. The functions take
   the liveness probe, the host, the boot id, and the clock as
   parameters, so the stale rules test without a real `/proc`. Rationale:
   `core.py` keeps its no-I/O charter, and the house pattern puts the
   pure part under test through injected inputs.
3. The stale rules, in examination order: the record does not parse, the
   schema version is unknown, the boot id differs, the pid is dead, the
   start time differs, or the acquire time is older than 24 hours. A
   foreign-host record with a young acquire time stays fresh. Rationale:
   each rule alone heals one wedge path, and the order puts the cheap
   field comparisons first.
4. The record write is one `write()` of the full payload right after the
   exclusive create. Rationale: a crash leaves a short file, a short file
   fails to parse, and a failed parse is stale, so the wedge path ends in
   a heal.
5. The holder label is `loop-<yyyymmddhhmm>-<4 hex>`. Rationale: two runs
   started in the same minute still differ, and the label is unique per
   run without a server.
6. The CLI contract: `scan [--holder LABEL]`, `acquire --holder
   LABEL`, `release --holder LABEL`, and `release --force` with or
   without the label. The acquire refuses a fresh foreign lock with
   exit 2 and the holder details on stderr. The release refuses a label
   mismatch with exit 2, takes no lock file as success, and `--force`
   skips the match. Argparse usage errors map to exit 64. Rationale:
   exit 2 keeps one category, and the operator gets one explicit
   destructive path that works without the lost label.
7. The halt step stays in the skill. The CLI gains no halt logic, because
   the halt contract resolves the file from the session root or the
   primary checkout, a path rule the CLI would have to duplicate.
   Rationale: the halt-gate hook already enforces the denial, and the
   skill step gives the run an explicit early stop.
8. No MCP wrapper. The lock is harness-facing, not model-facing. The
   skill documents the CLI.
9. The record stores the two times as ISO 8601 UTC strings, the schema
   version as the integer 1, and reads a missing version field as an
   unknown version. The boot id reads from
   `/proc/sys/kernel/random/boot_id`, and the start time reads from
   field 22 of `/proc/<pid>/stat`. An unreadable source counts as a
   mismatch, so the lock goes stale. Rationale: the shapes stay
   documented and every unreadable source ends in a heal.
10. One stderr line carries the first matched stale rule, the holder,
    the host, and the `release --force` remedy. Success on stdout stays
    silent for all three commands. An unreadable state directory exits
    2 on every command with the path and the remedy. Rationale: one
    report shape, and the loud failure names the fix.
11. A second acquire that carries the label of the lock in force is
    idempotent with exit 0 and no rewrite. Rationale: a re-entry in one
    run must not fail on its own lock.
12. The run releases the lock before the human spec gate wait, because
    the propose phase ends the run, and a lock held across the wait
    would age into the stale rules. Rationale: the release lands at the
    true end of the run, not at the pause.

## Failure modes

- A live but wedged holder never heals itself. The operator reads the
  stderr details, kills the holder, and releases with `--force`. The ADR
  states this residual.
- Two simultaneous acquirers of the same stale lock can both clear and
  take it. Both already concluded that no live holder exists. The race
  window is documented as best effort.
- An unreadable state directory fails the scan with exit 2, and the
  message names the path and the remedy. The loud failure beats a silent
  pass.
- A hung `gh` call stays out of scope here. The lock examination runs
  before the fetches, so a refused scan is instant.
- The git common-dir resolution runs once per CLI call. The cost is one
  subprocess spawn, far below any hook budget concern, because the CLI
  runs per command, not per event.

## Amendments during apply

The reality pass rewrote two mechanics. First, the record pinned the CLI
process id, and a CLI call dies at once, so every later call saw a dead
pid and the lock never refused a second run. The record now pins the
session anchor: the walk follows the parent chain from the calling
process to the first process whose name matches one harness name, and a
chain with no harness process records no pid, so an anchorless record
behaves like a foreign host and ages out. Second, the own-verdict gains
the anchor path beside the label path, so the session identifies its own
lock without repeating the label. The delta carries both amendments with
two new scenarios, and the regen ran after the spec edits.

## Entropy (ASIT)

- Unification: the lock rides the existing CLI contract and the house
  exit-code discipline, and the pre-flight steps extend the peak-window
  requirement pattern.
- Division: the stale judgment sits in `lock.py` over injected inputs,
  separate from the file I/O in the same module and from the classification in
  `core.py`.
- Breaking symmetry: the holder of the lock in force and a foreign
  caller get distinct treatment at the CLI edge, and `--force` marks the
  operator path at the same boundary.
- Object removal: no wrapper layer joins. The lock reuses the CLI
  entry, the runner seam, and the skill pre-flight. The ADR route
  replaces any edit to ADR 0012, which stays frozen.
- No new dependency and no new component kind beyond one module in an
  existing package.
