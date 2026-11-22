## Context

The analysis report `reports/2026-11-20-sim-harness-adoption.md` mapped the
SIM discipline of arXiv 2611.18856 onto this harness and the operator
approved the adoption design. Three moves carry it: attempt ledgers on
lesson records, consultation with teeth at plan time, and outcome write-back
at result review and at the merge hook. The host-memory lesson files and
their index live outside this repository. The repo owns the pipeline text,
the agent-memory kit text, and the merge-time hook.

## Goals / Non-Goals

**Goals:**

- A lesson record carries a problem line and an attempt ledger, so the next
  session reads the attempts, not just the rule.
- A plan cites the lessons of the surfaces it touches, and the review round
  holds the teeth.
- The run writes the observed outcome back on the lesson it cited, and the
  merge hook names that write-back in its nudge.
- Step 14 presents the write-back as shipped, with no skip conflict.
- The ten oldest host lessons convert during apply, host-side.

**Non-Goals:**

- No retrieval system and no embeddings. The index holds 34 lines and the
  sessions read it whole.
- No nightly learner. The dspy-gate nightly loop already covers governed
  modules.
- No automatic harness edits. The operator merge stays the gate.
- No ledger query tool. The deferral trigger: an index line first hides a
  problem a session needed.

## Decisions

### D1: The problem line is placement-agnostic in the requirement

The requirement pins the content: the lesson names its problem in one line.
The design prefers the top-level `problem:` frontmatter field. The Claude
Code memory contract defines the frontmatter shape, so the apply phase
writes one converted file and reads it back. If the harness strips the
field, the fallback is the metadata block, and the last fallback is the
first body line `Problem:`. The requirement stays placement-agnostic, so
the fallback changes no approved behavior.

### D2: The consultation teeth live in the review round

The operator settled this fork. No repo guard test, no plan-file convention,
and no hook enforce the citation. A plan that cites no lesson while it
touches a surface that owns one is a review finding for the adversarial
reviewers, one finding per plan, naming every uncited owning lesson.
Rationale: plans are not consistently files here, so mechanical enforcement
needs a new convention for thin value. The pull itself is a judgment on the
index lines, not a token match: the plan step reads the problem lines and
pulls the lessons whose problem names the touched surface by meaning. The
index-line format of requirement 7 makes the surface nameable.

### D3: The write-back routes through the surfaces that ship today

The result review (inner-loop step 4) appends the attempt during the run.
The merge-time hook repeats the nudge in its fixed string and keeps its
security shape. The hook matches the command line and never echoes it, and
the injected string stays fixed. The Step 14 amendment presents the
write-back as shipped, so the pipeline carries no step that contradicts its
own skip rule.

### D4: The conversion runs host-side in apply

The operator settled this fork. The ten oldest lessons by file mtime
convert to the ledger format, and their ten index lines gain the problem
and the setting. The remaining lines convert when their lessons convert.
Nothing mirrors into the repository. Seeded attempts follow the house
confidence discipline: the observation carries the evidence the file
already holds, the setting records the repo, host, or model the file
names, with `unrecorded` where the source names none, and no seeded field
is invented.

### D5: No new component kind enters this change

ASIT verdict: unification only. No guard test, no plan-file convention, no
retrieval system, no embeddings, no nightly learner. The only deferred
candidate is the ledger query CLI, and its trigger condition is recorded
under Non-Goals.

### D6: The audit report grows without a breaking pin

The negative-instruction-audit scan is read-only with no repo-count pins,
so the new prohibitive sentences in the pipeline text grow its report
without failing a gate. A later audit run can classify the new sentences.

## Risks / Trade-offs

- The consultation rule adds one read-and-cite act to every plan. The
  mitigations: the index loads into every session already, and the citation
  cites from the loaded index with no extra reads.
- The ledger adds lines to every lesson file. The mitigation: one attempt
  per exercised occurrence of the rule, and a verdict, so the file grows
  only when the run actually applies the rule and observes an outcome.
- The hook edit touches a protected path. The mitigation: the pull request
  body carries the acknowledgment line at creation time, and the operator
  merge is the acknowledgment.
- The harness may strip a nonstandard frontmatter field. The mitigation is
  the D1 fallback ladder, verified by a read-back in apply.

## Migration Plan

The repo change lands in one implementation PR, with the ADR beside it.
The host-side conversion runs in the apply phase of the same run and needs
no migration: the ledger format appends, so nothing deletes. A rollback
removes the pipeline text additions. The ledgers already written stay as
prose history.

## Open Questions

- None. The report settled the design, and the operator settled the two
  forks (the conversion home, and the teeth) during the grill of this
  proposal.

## Diagram

The improvement loop with the ledger. Dynamic view, lightweight
C4-inspired. ASCII is the house format. Recorded as an explicit assumption.

```text
+------------------+   pulls lessons whose problem      +----------------------+
| plan step        |   names the touched surface,       | MEMORY.md index      |
| (inner loop 1-2) |   cites them by name               | + lesson files       |
+--------+---------+                                    | (host memory dir)    |
         | run: gates, tests, reviews                   +----------+-----------+
         v                                                         ^
+--------+---------+   append attempt (holds | misled)            |
| result review    |----------------------------------------------+
| (inner loop 4)   |
+--------+---------+
         | merge
         v
+--------+---------+   fixed nudge: close the loop; write    +----------------------+
| merge hook       |   the cited-lesson outcomes back       | agent-memory store   |
| (PostToolUse)    |--------------------------------------->| (lesson issues,      |
+------------------+                                        | Mode 5 append)       |
                                                            +----------------------+
```

Boundaries and responsibilities:

- The host memory dir holds the ledger of record for harness lessons. The
  plan pulls from the index, and the result review writes back into the
  files.
- The merge hook carries no state. It repeats the nudge with its fixed
  string and keeps its match-and-echo security shape.
- The agent-memory store holds the session-side lessons. Mode 5 appends the
  attempt to the issue body, and Mode 6 stays out of lesson issues.
