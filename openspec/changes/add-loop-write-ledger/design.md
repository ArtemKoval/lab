# Design: add-loop-write-ledger

## Source

The requirement is proposal P4 of the dsh analysis. The adversarial
pair folded four blockers and five fixes into the artifacts: the marker
is fresh per write and never the holder label, the pending view keeps
every unconfirmed marker visible for the reconcile scan with the
superseded flags, the exit contract names its complete failure set, and
the resume rules cover label, merge, and close intents per kind. The
`-bot`-style overreach is absent here by design: the reconcile reads
the comment bodies for the literal marker, without the GitHub search
endpoint.

## Plan review

- The marker is fresh per intent, generated over an injected clock and
  random source, and regenerated on a collision. The holder label
  shares the textual form but lives in a different namespace, and the
  recipe embeds the marker in comments only.
- The superseded-marker hole: run A posts, dies pre-confirm, run B
  writes intent B, and a dedup-only view hides marker A from the
  reconcile, which double-posts. The pending view carries every
  unconfirmed intent with superseded flags, the reconcile confirms
  every marker it finds in the comment bodies, and the recipe forbids
  a second live intent for a group with one stderr note on the write
  action.
- The exit contract: 0 success, 64 usage, and the operational set is
  the unreadable store and the confirm-unknown-id. A missing store
  gives write a created store, pending an empty list at exit 0, and
  confirm the unknown-id failure.
- The per-kind resume rules answer the report's motivation line: a
  comment reconciles by the marker scan, a label retries as a re-add,
  and a merge or close retries with the tolerated already-done error,
  which confirms the intent. A superseded intent that can no longer
  confirm stays in the audit trail and out of the decision.
- The recipe runs the ledger commands under the run lock, and the
  single-writer rule is recipe discipline in the plan_exec manner, so a
  manual call stays an operator action. A ledger exit 2 mid-phase
  behaves like a gate failure, with one comment naming the fault and
  the next run resuming from pending.
- The comment embed keeps the fixed first line, so the fold rule and
  the loop-comment rule stay intact, and the reconcile fetch uses the
  issue comment bodies without the GitHub search endpoint.

## Diagrams

Format: ASCII in fenced blocks. Rigor: house precedent.

### Container diagram

```text
+-------------------------------------------------------------------+
| a loop phase run                                                  |
|                                                                   |
|  ledger write --> gh write (marker embedded) --> ledger confirm   |
|       |                |                                |         |
|       v                v                                v         |
|  +-----------------+  +------------------------+  +------------+  |
|  | ledger.jsonl    |  | GitHub (the write)     |  | confirmed  |  |
|  | in the state    |  | comment/label/merge/   |  | line       |  |
|  | dir (append-    |  | close                  |  |            |  |
|  | only JSONL)     |  +------------------------+  +------------+  |
|  +-----------------+                                              |
|                                                                   |
|  resume: ledger pending --> scan bodies for each marker           |
|          confirm found --> retry missing newest (same marker)     |
+-------------------------------------------------------------------+
```

### Component view

```text
+----------------------------------------------------------------+
| tools/process_issues/process_issues/                           |
|                                                                |
|  ledger.py  path from the lock state dir, newline-guarded      |
|             append, read with numbered skip notes, pending     |
|             view with superseded flags, id generation over     |
|             the injected clock and random source               |
|  cli.py     the ledger command with the action positional,     |
|             the flag checks, and the exit mapping              |
+----------------------------------------------------------------+
```

## Decisions

1. The store is one append-only JSONL file beside the lock, with the
   newline guard on every append, so a torn append cannot glue onto
   the next record. Rationale: the audit trail stays readable, and the
   glue is the real tear mode.
2. The marker is fresh per intent over an injected clock and random
   source, and the writer regenerates on a collision with an existing
   id. Rationale: two writes in one run share no marker, which closes
   the lost-write hole the reconcile would otherwise miss.
3. The pending view prints every unconfirmed intent with superseded
   flags, and the newest row of a kind+key group owns the decision.
   Rationale: the reconcile must see superseded markers, or a
   superseded-but-posted comment double-posts.
4. The exit contract: 0 success, 64 usage, and the operational set is
   the unreadable store and the confirm-unknown-id. A missing store
   gives write a created store, pending an empty list at exit 0, and
   confirm the unknown-id failure. Rationale: the failure set is
   complete and the spec pins failure lists exactly.
5. The per-kind resume rules: a comment reconciles by the marker scan,
   a label retries as a re-add, and a merge or close retries with the
   tolerated already-done error that confirms the intent. Rationale:
   each family gets the rule its API shape supports, and the report's
   motivation line (a label set, a comment posted, a merge done) stays
   covered.
6. The recipe runs the ledger commands under the run lock, and the
   single-writer rule is recipe discipline in the plan_exec manner.
   Rationale: no code ties the ledger to the lock, and a manual call
   stays an operator action.
7. A ledger exit 2 mid-phase behaves like a gate failure: one comment
   names the fault, the phase stops, and the next run resumes from the
   pending list. The skipped-line notes reach the run report.
   Rationale: one failure path serves the new component.
8. The loop comment keeps the fixed first line with the marker at the
   end of the body, so the fold rule and the loop-comment rule stay
   intact. Rationale: the fold reads the first line only.
9. The registry carries no new unit, because the module ships inside
   the existing process_issues unit. The unknown future event values
   fall to the skip rule, which carries the forward compatibility
   without a schema version field.

## Failure modes

- A torn append glues onto the next record. The newline guard prevents
  it, and a line that still fails to parse skips with a numbered note
  at exit 0.
- A confirm that never lands leaves the intent pending, and the next
  run reconciles it. The pending view is the detector.
- A manual `ledger write` outside the run lock. The recipe discipline
  covers the phases, and a manual call is an operator action with the
  same-value risk the stderr note surfaces.
- The reconcile fetch cost: one comment fetch per issue with pending
  intents. The fetch reads the comment bodies, and the recipe names
  the command form.
- A superseded intent that can no longer confirm stays pending in the
  audit trail. The superseded flag keeps it out of the decision.
- The confirmed lines accumulate at the cron rate of two fires a day.
  No rotation is in scope, and the unknown future event values fall to
  the skip rule.

## Entropy (ASIT)

- Unification: the state dir, the append-only form, the guard test,
  and the gate-failure path reuse the house seams. No new component
  kind beyond one module.
- Division: the pure ledger view over the raw lines, and the I/O at
  the CLI edge, with the id generation over injected inputs.
- Breaking symmetry: the decision view (newest-wins) and the audit
  view (every unconfirmed marker) are distinct reads of one store.
- Object removal: no reconcile subcommand, no effect queue, no backoff
  worker, no schema version field. The skill carries the reconcile
  rule, and the commands stay three.
- No new dependency.
