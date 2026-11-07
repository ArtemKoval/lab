# Council Notes: design.md

## Author Summary

The author draft settled the durable JSONL store beside the lock, the
one-command three-action shape, the newest-wins pending view, the
skip-with-a-note rule for bad lines, and the recipe steps with the
retry on the same marker.

## Reviewer Challenges

- BLOCKER: the marker form collides with the holder label and the
  draft never pinned a fresh value per write, which loses the second
  write of one run.
- BLOCKER: the newest-wins dedup hides a superseded marker that is
  already live in a posted comment, which double-posts.
- BLOCKER: the exit contract contradicted itself, and the failure set
  was incomplete.
- BLOCKER: the report names label, comment, and merge writes, and the
  draft reconciled comments only.
- SHOULD-FIX: the lock discipline for the ledger commands, the
  mid-phase failure rule, the invocation shape and key vocabulary, the
  marker inside the loop-comment rule, the pending output shape, and
  the Impact completeness.

## Resolutions

- Accepted: every blocker. The marker is fresh per write over injected
  inputs, the pending view keeps every unconfirmed marker with
  superseded flags, the failure set is complete, and the resume rules
  cover comment, label, merge, and close per kind.
- Accepted: the recipe discipline for the single-writer rule, the
  gate-failure behavior for a ledger fault, the second positional
  action, the marker at the end of the body behind the fixed first
  line, the pending payload fields, and the Impact list.
- Rejected: a reconcile subcommand, a schema version field, rotation,
  and a status surface, all as scope cuts with named reasons.

## Remaining Risks

- The reconcile fetch cost of one comment fetch per issue with pending
  intents.
- A superseded intent that can no longer confirm stays in the audit
  trail, out of the decision.
