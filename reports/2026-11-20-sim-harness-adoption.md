# Analysis: Self-Improvement Memory applied to the lab harness

- Source: arXiv 2611.18856, "Self-Improvement Memory Enables Continual
  Recursive Self-Improvement", Yu et al., Google Cloud AI and Google
  DeepMind, submitted 2026-11-13. Read in full from arxiv.org/html.
- Date: 2026-11-20
- Status: analysis only. Nothing in this report changes the harness. The
  adoption design in section 3 needs an approved OpenSpec change of its own.
- Confidence marks: **observed** = read here or run here. **derived** =
  follows from the mapping in section 2. **inferred** = a prediction that
  section 5 records for a later check.

## 1. The paper in brief

The paper studies Continual Recursive Self-Improvement (CRSI): harness
optimization that continues after the benchmark or the policy model changes.
An evolved harness alone does not say why its edits exist or how they
performed. The next optimization round therefore repeats old attempts, or
changes inherited parts blind, or attributes an inherited edit to its own
round.

Self-Improvement Memory (SIM) is a record for the harness optimizer, not for
the task-solving agent. Its shape:

- One entry per recurring harness problem (a root-cause hypothesis such as
  "premature completion without execution verification").
- Each entry holds ordered attempts. An attempt records the modification
  with its rationale, the predicted outcomes written before evaluation, the
  observed outcomes written after, and provenance (domain, benchmark,
  policy, round).
- The loop records only a selected edit of each round. A selected edit that
  fails, and a selected edit that a later round replaces, keep their records
  and their unresolved predictions (the paper's Appendix D.3 defines the
  fields). A candidate that the selector rejects gets no record.
- The proposer and the selector read the whole record at every round. No
  retrieval and no truncation. The guidance: reuse the rationale and
  reassess the edit after a setting change, and weight task-specific
  evidence more when the setting is similar.

Results, on the paper's four domains: full SIM beat harness-only
continuation in all six cross-dataset settings and in all four
model-transfer settings. Across ten paired coding continuations from
independent source runs, the mean advantage is 2.36 points over
harness-only continuation. The p-value is 0.003. Nine of the ten pairs
favor SIM. The sharpest finding for this lab: memory that carries only the
diagnoses (the rules) without the evidence scores below no memory at all in
one setting, and helps unevenly in others. **observed** — read from the
paper.

## 2. What our harness already holds

The lab harness is the feature-pipeline skill, the Claude Code surface
(skills, hooks, permissions), the two memory stores, and the gate tools.
The paper's components map onto parts that already exist:

| Paper component | Our component | State |
| --- | --- | --- |
| Optimizer loop: proposer, selector, evaluator | The inner loop (plan, review, implement, review) with the adversarial pair, plus Step 14 (Log, Analyse, Handover, Reflect, Improve) | The loop skeleton exists. Analyse and Reflect stay unshipped by design until their tooling exists. **observed** |
| Cross-model CRSI (the policy changes) | Claude Code version bumps, the z.ai path that serves one model behind every label, and the other hosts in the fleet | Real and recurring. A lesson tuned on one host or model can mislead on the next. Several memory files carry host scopes for exactly this reason. **observed** |
| Cross-dataset CRSI (the tasks change) | The task mix moves: game ports, then crm ports, then the upstream contribution, then deployment work | Real. A crm-port lesson can mislead inside a game port. **observed** |
| SIM entry | The host-memory lesson file: a rule line, evidence, a How-to-apply line, and links | Close. Gaps: no predicted-versus-observed structure, no provenance fields, no attempt ledger. Appends happen by accident, not by rule. **observed** |
| Proposer and selector read the full record | Inner-loop step 2 says "consult prior lessons first". MEMORY.md loads into every session | Consultation stays a nudge, not a named mechanical act. The index carries hooks, not problem plus evidence. **observed** |
| Diagnoses without evidence do harm | The `memory:lesson` issues of the agent-memory store: imperative rules | The kit demands evidence in the body, but no format demands outcomes or provenance. **observed** |
| A selected edit that fails or gets replaced keeps its record | A lesson the team adopted and later reverted or replaced leaves its outcome behind. The trail lives at best in the Friction section of the telemetry block in a handover issue, and in the Step 14 Reflect checklist item "a fix that took several attempts" | Partial. The ugrep lesson carries two failed watcher attempts. Most adopted-then-replaced edits leave no outcome record. **observed** |
| Held-out discipline (the verifiers stay frozen) | The gates and the gate-integrity guard. The specs are the source of truth | Already handled. A harness change cannot silently game its own evaluator. **observed** |

## 3. The adoption design

The design makes three moves. First, lesson records grow attempt ledgers, so
each record carries predicted outcomes, observed outcomes, and provenance.
Second, the pipeline text names lesson consultation as a mechanical act at
plan time and at merge time. Third, the next occurrence of a problem records
the observed outcome on the lesson it cited.

ASIT verdict: no new kind of component. The memory files, the index, the
pipeline text, and the merge-time hook all exist today. The design unifies
them. **derived**

### 3.1 V1 — the record format (the memory files)

A lesson file keeps its name and its rule line. The body gains an attempt
ledger. A "re-bit" line names one recurrence of the problem after the lesson
existed:

```text
## Attempts
- 2026-11-07, session 749ef353: trigger <what recurred>;
  prediction <what the rule promised>; observation <what happened>;
  setting <repo, host, model>; verdict holds | misled | superseded
- 2026-11-20, session 7c8e3e6c: ...
```

The frontmatter gains one field, `problem:`, the recurring problem in one
line (for example: "a gate exit code never decides a step when a pipe hides
it"). The rule line stays the headline of the file.

Two files already carry this shape in prose. `mutation-lcov-freshness.md`
holds three vacuous shapes, and `gate-exit-codes-die-in-pipes.md` gained a
re-bit line on 2026-11-20. The change makes that shape a rule, not an
accident. **observed**

The MEMORY.md index line gains the problem and the setting, and stays one
line in the file's real shape:

```text
- [Gate exit codes die in pipes](gate-exit-codes-die-in-pipes.md) — any
  gate, any chain: the pipe's exit decides, not the gate's; run it bare
```

The agent-memory kit's Mode 5 gains the same rule for store lessons: on the
first recurrence of a lesson, append the attempt (trigger, prediction,
observation, setting, verdict) to the lesson issue body. The cache slice and
the standard session reads never show a comment. The lesson body reaches
every future session.

### 3.2 V2 — the consultation wiring (the pipeline and hook text)

- Inner-loop step 2 names the act: read the index, pull every lesson whose
  problem names the step's surface, and cite the pulled lessons in the plan.
  A plan that cites no lesson while it touches a surface that owns one is a
  review finding.
- The write-back routes through the surfaces that ship today: the
  inner-loop result review (step 4) appends the attempt when a cited lesson
  holds or misleads during the run, and the merge-time hook repeats the
  nudge. A miss opens no new file unless the problem is new.
- Step 14 mandates a skip for Reflect until its tooling exists. The
  OpenSpec change amends that skip rule for the write-back in the same
  change that adds it, so the pipeline never carries a step that contradicts
  its own skip rule.
- The merge-time hook is `.claude/hooks/agent-memory-task-complete.sh`. The
  path sits inside the protected set of the gate-integrity guard
  (`tests/claude_infra/test_gate_integrity.py` guards `.claude/hooks/*`).
  The pull request that edits it carries the `gate-integrity: acknowledged`
  line in its body at creation time, and the operator merge is the
  acknowledgment.

### 3.3 V3 — the ledger query (deferred, with a reason)

A `tools/sim_ledger` CLI (inspect shape: render problems with unresolved
predictions) is the only candidate new component. Defer it. The index holds
34 lines today, the sessions read it whole, and no current friction needs a
query. Add the tool when an index line first hides a problem a session
needed. **observed** for the line count, **derived** for the deferral — the
removal tool beats the addition tool here.

## 4. What stays out, and why

- No retrieval system and no embeddings. The paper reads the whole record
  every round. Our index is small enough for the same discipline.
  **derived**
- No nightly learner. The dspy-gate nightly loop already learns behind the
  freeze for governed modules. SIM governs judgment records, not model pins.
  **observed**
- No automatic harness edits between rounds. The paper's optimizer edits
  code without a human gate. Our Improve step keeps the operator merge, and
  the gate-integrity rule keeps protected paths behind the operator
  acknowledgment. The paper's Ethics Statement carries the matching warning:
  "A self-modifying harness could satisfy an evaluator without solving the
  intended task." **observed**

## 5. Predictions, recorded now

The paper records each edit's prediction before evaluation. This report
applies the same discipline to itself.

- P1 **inferred**: with provenance on the index line, lessons misapplied
  across hosts and task types drop below one per month. The baseline sits
  at one in the last two weeks (the pipe lesson re-bit today across a
  background-chain shape). Probe: once a month, run
  `grep -rn "verdict misled" <memory-dir>` and read the new attempt lines.
  The count lands in the next analysis report in this directory.
- P2 **inferred**: at least one existing store lesson misleads once before
  2027-03. This prediction needs the V2 write-back, so it becomes
  checkable only after that change merges. Until then it stays on record
  with no probe.
- P3 **inferred**: the V2 consultation adds no measurable latency to a plan
  step. Probe: after the change merges, compare the wall time of five plan
  steps that cite lessons against five plan steps from before the change,
  from the cc-logging durations in `.cc_logging/`.

## 6. Follow-ups

1. Open the OpenSpec change for V1 and V2 (a new capability,
   `harness-improvement-memory`), grounded on this report. The change
   touches four surfaces: the feature-pipeline text (inner-loop step 2, the
   result review, and the Step 14 skip rule), the agent-memory kit text
   (Mode 5), the merge-time hook (with the `gate-integrity: acknowledged`
   line in the pull request body), and the Step 14 Analyse or Reflect
   placement if the write-back needs a named home there. The memory-file
   format itself lives outside this repository, so the kit text owns the
   format rule, and any repo-side guard reads only repo-owned surfaces. A
   host without the memory directory skips the format check the way the
   setup doctors skip their absent units.
2. Convert the ten oldest host-memory lessons to the V1 format inside that
   same change. The format then starts with content, not with an empty
   rule.
