# Analysis: Elephant-Goldfish Model applied to the lab harness

- Source: google/elephant-goldfish-model, plugin name `egm`, v0.1.1 (release
  published 2026-11-06), Apache-2.0, Python, 22,009 stars at the count of
  2026-11-22, latest push 2026-11-21. Read through the GitHub contents,
  releases, and tags endpoints on 2026-11-22.
- Date: 2026-11-22
- Status: analysis only. Nothing in this report changes the harness. The
  recommendation in section 3 needs an operator decision and, if adopted,
  a feature-pipeline change of its own.
- Confidence marks: **observed** = read here or run here. **derived** =
  follows from the mapping in section 2. **inferred** = a prediction that
  section 5 records for a later check.

## 1. The plugin in brief

EGM is a plugin for AI coding assistants. The README states the division of
roles. The Elephant is the primary agent. It holds the project context and
drafts the specification. The Goldfish reviewers are subagents with no
earlier conversation. Each one examines the draft and the files that the
draft references, and reports unstated assumptions and blind spots. The
human approves the specification before implementation starts. **observed**

The install for Claude Code is two commands: `claude plugin marketplace add
google/elephant-goldfish-model` and `claude plugin install egm@egm`. The
harness doc demands a full-plugin install. A skills-only copy breaks,
because the skills read `agents/` and `resources/document_standards/` at
run time. **observed**

The plugin ships 8 skills, 10 reviewer personas, and 5 document standards.
The skills are egm-bootstrap, egm-brainstorm, egm-draft, egm-drift-report,
egm-lite, egm-resolve, egm-review-loop, and egm-review. Every skill
frontmatter carries `disable-model-invocation: true`, so a skill runs only
on an explicit `/egm:` command. **observed**

The review core is `/egm:egm-review`. It runs five stages: an initial
zoom-out, a comprehension test, a design critique, an intermediate zoom-out,
and an implementation-readiness test. Each stage pairs a reviewer roster
with one document standard. At full flow it makes about ten reviewer runs in
five stage dispatches. Each finding carries a severity (blocker, major,
nit), line numbers, and a stable id. The loop allows one re-audit per stage.
The loop records a reviewer that fails twice as "not run", never as a
reviewer with zero findings. **observed**

`egm-drift-report` is the smallest skill. It runs in one context and spawns
no subagents. It reads each document in a folder, finds the code that each
document names, reads that code, and reports only the differences in four
classes: missing features, incomplete models, logic shortcuts, and
architectural divergence. It writes one dated report file. **observed**

Google applies the plugin to its own feature work. The AI_POLICY demands a
design-doc pull request with a `design-ready` label for a feature above 100
non-test lines, and a `pr-ready` label before the implementation pull
request. The repo holds 19 design docs under `docs/designs/`. **observed**

## 2. What our harness already runs

The lab harness is the feature-pipeline skill, the Claude Code surface, the
OpenSpec flow, and the gate tools. The EGM components map onto parts that
already exist:

| EGM component | Our component | State |
| --- | --- | --- |
| Elephant draft flow (egm-brainstorm, egm-draft) | Step 1.5 with `/opsx:propose`, `grill-me` for clarification, `design.md`, and a decision tournament for a genuine fork | Covered. A second draft flow would fork the design-decision record. **observed** |
| Goldfish fresh-context review (the comprehension stage reads the document alone) | The adversarial-authoring pair: `adversarial-author` drafts, `adversarial-reviewer` challenges in its own context. Step 12 verifies each finding with independent skeptics. The Step 1.5 builder check gives one fresh agent only the change artifacts | The fresh-context principle already runs here in another shape. The named paraphrase act is new and small. **observed** |
| Per-document-type standards and reviewer rosters (5 standards, a named roster per stage and per document type) | One generic `adversarial-reviewer` persona. Step 12 names the review dimensions in prose | Real delta. The house review names dimensions, not standards files and rosters per document type. **observed** |
| egm-review-loop verdicts (severity, stable ids, PROPOSE FIX or CONTEST, the "not run" rule, the re-audit cap) | Step 12: verify findings, fix the confirmed ones, answer a wrong finding with technical reasons, at most 2 refinement rounds with a new external signal | Strong overlap in spirit. The structured verdict vocabulary and the failed-reviewer accounting are new, and both are small. **observed** |
| egm-drift-report (a folder-wide doc-versus-code divergence sweep) | `verify-change` checks one change at archive time. Step 12 checks doc-versus-code consistency on the diff only. spec-mining mines coverage, not drift | No house equivalent. This is the strongest delta. **observed** |
| Two-stage label governance (design-ready, pr-ready) | The proposal-PR-first rule in `openspec-git-discipline`: the proposal PR merges before implementation starts | Already handled in another shape. **observed** |
| egm-bootstrap (a subtree README sweep) | Step 6: a README for each tool | Covered for new work. A sweep adds little to a repo with one README convention. **derived** |
| egm-lite (a light 5-step protocol) | `fast:` mode | Covered. **observed** |
| Plugin packaging (one skill set, a marketplace, many harnesses) | Committed skills, the gate-integrity guard, the setup registry | A packaging idea, not a review idea. A user-level plugin sits outside this repository's version control. **observed** |

The honest delta: the fresh-context principle, the review loop, and the
human approval gate already run here in another shape. The genuinely new
pieces are the per-document-type standards with rosters, the structured
verdict vocabulary, egm-drift-report, and the packaging. **derived**

## 3. The adoption options

### 3.1 Option 1 — install the plugin and run its commands as the house flow

The user-level install adds every command to each session. Rejected as the
end state, for these reasons:

- Governance: a plugin update changes prompts with no pull request and no
  gate. The house runs committed skills, and the gate-integrity guard reads
  repository paths only. **observed** for the guard scope, **derived** for
  the update path
- Cost: one full `/egm:egm-review` run makes about ten reviewer runs. Step 12
  uses one dispatch for the same diff. On the z.ai path, every dispatch
  burns credits, and a model label changes no served model. **derived**
- Overlap: the draft flow, the review loop, and the approval gate duplicate
  Step 1.5 and Step 12. Two review machineries in one repo invite drift
  between them. **derived**
- Style: EGM writes its own plain-English standard. It bans jargon and
  promotional adjectives, which agrees with the house goal, but it controls
  no sentence length, tense, or voice. Committed prose here follows
  ASD-STE100. **observed** for the EGM standard, **derived** for the mismatch

The install itself stays useful as the probe vehicle in section 3.4, because
the dormant skills change no repo file and run only on an explicit command.
**observed**

### 3.2 Option 2 — port the ideas into house surfaces

The Unification move extends the `adversarial-authoring` skill with
per-document-type standards and extends spec-mining with a drift sweep.
This keeps STE, version control, and the gates. Rejected for now: the build
starts before any evidence that the EGM review quality is worth the cost.
The drift sweep needs judgment, so it is a new model-backed surface in any
option, and a port duplicates what EGM already ships and dogfoods. Keep this
option as the follow-up when the probe shows recurring drift. **derived**

### 3.3 Option 3 — hybrid, and the recommendation

Install the plugin at user level for egm-drift-report only. Keep the house
machinery (`grill-me`, the adversarial pair, the tournaments, Step 12) for
every spec and plan review. This is the recommendation.

- Governance: the plugin changes no repo file. The dormant skills run only
  on an explicit command. The protected gate paths stay untouched. The
  scope stays one command. **observed**
- Trust: the prompts are readable upstream before any install, and the
  source is Google under Apache-2.0. The reviewer personas read repository
  files. egm-resolve edits only the document under review, and it runs only
  inside a loop the operator starts. The house hooks and permissions still
  govern the session. **observed**
- Cost: the drift sweep runs in one context and spawns no subagents. The
  expensive review commands stay out of the default flow. **observed**
- ASIT: no existing house component detects doc-versus-code drift across a
  folder. spec-mining mines coverage, and `verify-change` checks one change
  delta. The sweep is a genuinely new kind of surface, so the smallest move
  is the plugin command with no build, and a port follows only on evidence.
  **derived**

### 3.4 The first probe

Smallest real test: one `/egm:egm-drift-report` run over one spec capability
folder with live code, `openspec/specs/peak-hours-gate/`. The run is
model-backed, so run it outside the peak window (Monday to Friday, 14:00 to
18:00 Singapore time).

1. Read the eight skill files and the ten persona files at tag v0.1.1
   upstream.
2. Install the plugin with the two commands from the README.
3. Run `/egm:egm-drift-report openspec/specs/peak-hours-gate`.
4. Verify each reported finding against `tools/peak_hours_gate` before you
   accept it.
5. Restate the findings in STE in a probe note under `reports/`, and record
   the wall time from `.cc_logging/`.
6. Keep the raw EGM report file out of the committed tree.

Cost: one session, one context, sequential reads of one spec file and one
tool tree. No subagent swarm. A good result shows findings that name real
divergences with files and symbols, no fabricated findings on matched
behavior, a wall time within a normal session step, and writes only to the
dated report file. A "No drift detected" result is also informative: it
dates the agreement between the spec and the code. **derived**

## 4. What stays out, and why

- No adoption of the Elephant draft flow. Step 1.5 with `grill-me` owns
  ideation and the proposal. A second draft flow forks the record between
  `design.md` and `design_draft.md`. **derived**
- No adoption of egm-review or egm-review-loop as the house review
  machinery. The adversarial pair and Step 12 cover the same principle at a
  fraction of the dispatch count. **derived**
- No adoption of egm-bootstrap and egm-lite. Step 6 and `fast:` mode cover
  them. **observed**
- No adoption of the design-ready and pr-ready label governance. The
  proposal-PR-first rule already carries it. **observed**
- No EGM artifact under `openspec/changes/`. The dspy-gate flow owns
  governed capabilities there, and the spec STE hook denies a non-STE write.
  **observed**

## 5. Predictions, recorded now

- P1 **inferred**: the probe over `peak-hours-gate` returns "No drift
  detected" or only nit-level findings, because the capability is young and
  its gates hold it. Probe: the run in section 3.4.
- P2 **inferred**: a sweep over the ten oldest capabilities finds at least
  one true divergence, because `verify-change` checks only the change delta
  at archive time and nothing re-checks a capability after later changes
  land. Probe: extend the sweep one capability at a time after the first
  run, and verify each finding.
- P3 **inferred**: one full `/egm:egm-review` run costs at least three times
  one Step 12 dispatch in wall time, because it makes about ten reviewer
  runs against one. Probe: if the operator runs it on one house report,
  compare the cc-logging durations.

## 6. Follow-ups

1. Trust audit before any install. Next action: read the eight skill files
   and the ten persona files at tag v0.1.1 upstream, and record the audit
   result in the probe note.
2. Run the first probe from section 3.4. Next action: install, run the
   drift sweep on `openspec/specs/peak-hours-gate/` outside the peak
   window, verify the findings, and write the STE note under `reports/`.
3. Decide keep or port from the probe evidence. Next action: if the
   operator keeps the plugin, open a feature-pipeline change that names the
   drift-report scope in CLAUDE.md. If the operator ports, ground the
   change on the probe note, and extend spec-mining or add a house drift
   skill.
4. Open a handover issue after the probe run. Next action: use the
   `handover` template with the telemetry block, per Step 13.
