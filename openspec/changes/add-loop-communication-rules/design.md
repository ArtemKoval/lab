# Design: add-loop-communication-rules

## Source

The requirement is proposal P5 of the dsh analysis. The adversarial
pair settled three decisions. The pick comment posts once per issue,
at the first pick. The `On it:` line names the object and the expected
result, behind the fixed first line. The informational path collapses
the acknowledgement into the answer comment. The change adds no
component. The rules live in skill prose, and one guard test holds the
order.

## Plan review

- The report says this lab starts with written rules. No code gate
  joins this change, and the mechanical limit stays with a later
  change.
- The pick comment is a loop comment. The fixed first line stays
  first, and the `On it:` line follows it. The fold rule and the
  ledger marker rule hold with no edit.
- The ledger needs no new requirement. The live spec wraps every loop
  GitHub write in the ledger steps, and the pick comment is one of
  those writes.
- The pick comment posts once per issue. A resume or a repair does not
  post a second acknowledgement, and the ledger reconcile covers a
  lost pick comment through its marker.
- The informational path posts the answer only. The answer itself
  names what the loop did, and a second comment adds noise to the
  quietest path.
- The silence rule names progress comments. The phase result, the
  gate-failure comment, and the pause question stay outside the rule,
  because each one carries a result or a stop.
- The feature-pipeline section sits before the review steps, so the
  rules govern the review traffic.

## Diagrams

Format: ASCII in fenced blocks. Rigor: house precedent.

### The pick comment anatomy

```text
+-----------------------------------------------------------+
| process-issues loop                          (fixed line) |
| On it: propose add-x from issue 15 and stop at the        |
|        spec gate.                               (the line)|
| <!--process-issues:MARKER-->                   (the marker)|
+-----------------------------------------------------------+
```

### The traffic line

```text
pick comment --> (silence) --> phase result
     |                             |
ledger write                 ledger confirm
```

## Decisions

1. One pick comment per issue, at the first pick. Rationale: one
   acknowledgement per request, and the ledger reconcile restores a
   lost pick comment through the same marker.
2. The `On it:` line sits behind the fixed first line, with the marker
   at the end. Rationale: the fold rule and the loop-comment rule stay
   intact with no edit to them.
3. The informational path posts no pick comment. Rationale: the answer
   comment serves the request, and a second comment adds noise to the
   quietest path.
4. The silence rule names progress comments. Rationale: the phase
   result, the gate-failure comment, and the pause question carry a
   result or a stop.
5. The feature-pipeline section sits before Step 11, not in the
   Cross-cutting rules block. Rationale: the report places the rules
   near the review steps, and the Cross-cutting block governs every
   step by its own rule.
6. The guard test holds the pick order and the form, not a code gate.
   Rationale: the rules live in recipe prose, and the skill guard
   pattern carries them.
7. No registry unit, no code module, and no README change. Rationale:
   the CLI has no new command, and the README documents the CLI.

## Failure modes

- A run picks an issue and dies before the pick comment posts. The
  ledger intent stays pending, and the resume reconcile scans for the
  marker and retries the write with the same marker.
- A run posts the pick comment and dies before the confirm. The marker
  sits in the comment, and the reconcile confirms it with no second
  post.
- A person reads the pick line as a promise of speed. The line names
  the object and the expected result, and it carries no time promise.
- The rules drift between the two skills. The feature-pipeline section
  names the pick step, and the guard test holds the skill text.
- An overlong pick line appears. The written rule caps nothing in this
  change. The report names the word budgets, and a later change can
  add the mechanical limit.

## Entropy (ASIT)

- Unification: the loop comment shape, the ledger steps, and the guard
  pattern carry the new rules. No new component kind.
- Object removal: no code gate, no word budget, no reply-gate module,
  and no new comment kind. The skills and the guard carry the change.
- No new dependency.
