## 1. Pipeline text

- [x] 1.1 Inner-loop step 2 carries the consultation act: pull every lesson
  whose problem names a touched surface, cite each by name in the plan, and
  name the review finding for an uncited plan on an owned surface.
- [x] 1.2 Inner-loop result review (step 4) carries the write-back: append
  the attempt to every cited lesson the run confirmed or refuted, in the
  same session, and open a new lesson only for a new problem.
- [x] 1.3 Step 14 carries the amendment: the Reflect sub-step presents the
  write-back clause as shipped, and the header skip text names the
  write-back exemption alone. The reflection skill and the Analyse
  sub-step stay skipped under the header rule.

## 2. Agent-memory kit

- [x] 2.1 Mode 5 carries the recurrence rule: the first recurrence of a
  store lesson's problem appends one attempt (date, session, trigger,
  prediction, observation, setting, verdict) to the lesson issue body, with
  the earlier body text unchanged. The Mode 5 format line grows
  accordingly: the body carries the rule, the evidence, and the attempt
  ledger once a recurrence exists.
- [x] 2.2 Mode 5 carries the host-lesson format rule beside its host-memory
  routing line: a new host lesson names its problem in one line, and its
  attempt ledger appends only, with the seven attempt fields. The kit text
  owns the format rule, and no repo file pins the host files.

## 3. Merge hook

- [x] 3.1 The fixed nudge string gains the write-back line. The matching
  logic, the echo protection, and the fail-open behavior stay unchanged.
- [x] 3.2 Verify the nudge by piping one synthetic merge event into the
  edited script from this worktree and asserting the write-back line in the
  returned `additionalContext` JSON. The live confirmation rides the
  archive merge of Step 13.

## 4. ADR

- [x] 4.1 Land `adr/0021-harness-lessons-carry-attempt-ledgers.md` in the
  house custom format, with the rejected options in the Decision prose.

## 5. Host-side conversion (outside this repository)

- [x] 5.1 Decide the problem-line placement by read-back: write one
  converted file, read it, and fall back from top-level frontmatter to the
  metadata block to a first body line when the harness strips the field.
- [x] 5.2 Convert the ten oldest host lessons by file mtime to the ledger
  format, seeding each ledger from the evidence the file already carries.
  Seeded fields follow design D4: the observation carries the held
  evidence, the setting records what the file names with `unrecorded`
  where the source names none, and no seeded field is invented.
- [x] 5.3 Rewrite the ten converted lessons' index lines in MEMORY.md with
  the problem and the setting, in the file's real link shape, and each line
  stays one line.
- [x] 5.4 Read back all ten converted files and assert each carries the
  problem line and one attempt with the seven fields.
- [x] 5.5 Render-check the ten rewritten index lines in MEMORY.md.

## 6. Verification

- [x] 6.1 The root hermetic suite passes, with `tests/claude_infra` green
  on the protected-path guard.
- [x] 6.2 `openspec validate harness-improvement-memory --type change
  --strict` passes, and the spec STE gate passes on the openspec tree (the
  worktree gap makes the manual run mandatory).
- [x] 6.3 One dry run proves the loop end to end, and this apply run is
  that dry run. The plan cites the owning lessons of the surfaces it
  touches. The run exercises the `spec-ste-hook-worktree-gap` lesson (the
  manual STE gate before push) and records its first attempt with the
  verdict holds when the gate catches what the hook missed.
