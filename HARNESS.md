# HARNESS — the setup around the agents

This document states what this lab builds around the agents that build the
product, and why. The product of this assignment is the library domain of the
crm engine. The deliverable is the setup: the harness in `.claude/`, the
spec flow in `openspec/`, the gate tools in `tools/`, and the evidence in
`.cc_logging/`. The assignment brief lives in issue
[ArtemKoval/library_crm#1](https://github.com/ArtemKoval/library_crm/issues/1).

## The three phases of this assignment

### Inception — intent to units of work

The intent lands as one OpenSpec change. The pipeline skill turns each
request into a change under `openspec/changes/<name>/` with `proposal.md`,
`design.md`, a spec delta, and `tasks.md`. Each `tasks.md` line is one unit
of work. The units name their files, their tests, and their gate. The
`tools/plan_exec` CLI extracts one brief per task and keeps an append-only
execution ledger, so an agent consumes one unit at a time with no human in
the loop. The proposal pull request merges to `main` before any
implementation starts. The `openspec-git-discipline` skill owns that gate.

### Construction — the flow per unit of work

Each unit of work runs through one flow:

1. Extract the brief with `tools/plan_exec`.
2. Write the test first, and see it fail.
3. Write the smallest code that passes the test.
4. Run the gates: coverage, complexity, mutation, duplication.
5. Commit one atomic change with a conventional message.
6. Tick the task in `tasks.md` and append the ledger line.

The flow lives in three places: the `library-uow` slash command
(`.claude/commands/library-uow.md`) drives one unit end to end; the
`senior-dev` and `senior-qa` agents own implementation and acceptance; the
`test-driven-development`, `systematic-debugging`, and
`verification-before-completion` skills own the discipline inside each step.
The `crm-onboard-domain` skill owns the five pack steps: extract, generate,
validate, smoke, review.

### Observability — what this setup tracks, and why

| Signal | Where it lives | Why we track it |
| --- | --- | --- |
| Every tool call and permission event | `.cc_logging/`, from the `cc-logging` hook | The run must explain itself after the fact; the telemetry block in each handover issue comes from this log. |
| Execution ledger per unit | `tools/plan_exec` ledger in the change folder | A long apply run must stay resumable, and each step must leave a record. |
| Coverage, complexity, mutation, duplication | `crapper`, the ruff complexity rule, `mutator`, `dryer` gate tools | A green suite alone proves too little; these gates bound the quality of new code. |
| Spec conformance | `openspec validate --strict`, the `spec-ste-gate` hook | The specs are the source of truth, and their text obeys one rule set. |
| Product accuracy | `crm` runs, evaluations, and the scoreboard | The case agent must match the held-out worker decisions; the scoreboard shows the score per run. |
| Handover telemetry | `tools/handover_telemetry`, one block per handover issue | The next run starts from numbers, not from memory. |

## Key decisions, and why this over that

- **Domain pack over a standalone app.** The assignment asks for a small
  library system. The engine already runs a queue, auth, sign-off, runs,
  evaluations, and a scoreboard, and reads every domain word from a pack.
  Onboarding library as a pack gives the full agent-facing product without
  one engine edit. A standalone FastAPI app would rebuild all of that.
- **Award = loan term in days.** The engine contract carries one numeric
  outcome per pack. The library pack maps the award to the loan term in
  days. The sign-off gate then guards loan terms over the standard 14 days,
  which keeps the approval limit setting meaningful.
- **Decline rules live in policy, and evals measure them.** The engine's
  pure rules module computes the outcome for approved cases only. The copy
  availability rule and the three loan cap sit in the wording, and the eval
  set pins the expected decision for each seed case. This is the house
  pattern: deterministic arithmetic in rules, conduct rules in policy,
  accuracy in evals.
- **Merge commits over squash merges.** The assignment ground rules demand
  small commits and no history rewrite, and CLAUDE.md asks for squash
  merges. ADR 0010 records the override: pull requests to `main` merge with
  merge commits for the duration of this assignment.
- **edge-tts over a cloud video service.** The four presentations are
  generated files: slide images from a script, narration from `edge-tts`,
  one `ffmpeg` mux per video. The tool is `tools/slidecast`, and the
  artifacts live in the repository. No external service holds them.

## What failed, or was abandoned

- The first session found Docker access denied for the workspace user. The
  fix is `sudo docker` for the devcontainer and floci runs, and the run
  notes record it.
- The GitHub wiki of this repository stays disabled: the repository is
  private, and private repositories on the free plan carry no wiki. The
  admin API refuses `has_wiki: true` for it. The wiki pages instead live in
  version control at `docs/wiki/`, with the screenshots beside them, which
  keeps them reviewable and linked from the code they document.
- The plan to run the whole Playwright suite against the library pack was
  abandoned. The suite pins insurance worker emails and case ids, and a
  full pack swap breaks those fixtures. The library pack instead gets its
  own e2e spec that signs in a library worker and walks the loan desk flow,
  while the default suite stays on insurance.

## What this run cut, and the reasoning

The assignment asks us to prioritize under a timebox, and these cuts are
deliberate.

- **Borrower self-service portal.** The engine gives workers a sign-in, and
  customers hold no login. Search by title or ISBN and the view of own
  loans need a borrower identity and new routes, so they stay out. Next
  step: a pack-scoped read-only borrower API plus a small SPA page.
- **Librarian writes to accounts and inventory.** The engine serves
  customer reads for the copilot, and the desk adds loan requests through
  intake, not through CRUD forms. Account and copy management stay out of
  this run. Next step: pack-scoped intake endpoints behind the worker
  role.
- **Password change, profile editing, system admin role, librarian
  account management.** Out of scope by the assignment text.

Each cut names its next step, and the handover issue carries them as
follow-ups.

## Hours spent

The `cc-logging` hook records every session event, and the telemetry block
in the handover issue carries the run numbers. This assignment started at
2026-10-31 20:27 UTC, with the first tool call of the session. The run log
below lists the wall-clock checkpoints of the phases, from the merged pull
requests.

| Phase | Started (UTC) | Ended (UTC) | Duration |
| --- | --- | --- | --- |
| Harness and inception (PR 2, PR 3) | 2026-10-31 20:27 | 2026-10-31 20:56 | 0 h 29 min |
| Domain pack implementation (PR 4) | 2026-10-31 20:56 | 2026-10-31 22:19 | 1 h 23 min |
| Archive (PR 5) | 2026-10-31 22:19 | 2026-10-31 22:22 | 0 h 03 min |
| Devcontainer, floci, screenshots | 2026-10-31 22:22 | 2026-10-31 22:30 | 0 h 08 min |
| Videos, wiki, handover (PR 7, issue 6) | 2026-10-31 22:30 | 2026-10-31 23:10 | 0 h 40 min |
| Readme and the scene layer (PR 9 to PR 13) | 2026-10-31 23:18 | 2026-11-01 00:52 | 1 h 34 min |
| Architecture wiki and the flow shots (PR 14) | 2026-11-01 00:52 | 2026-11-01 11:09 | 2 h 30 min* |
| One command in the devcontainer (PR 15) | 2026-11-01 11:09 | 2026-11-01 12:11 | 1 h 02 min |

The wall clock of the assignment is about 7 h 49 min across the phases
above, including the idle gap overnight between the scene-layer merge and
the architecture run (marked with *). The session telemetry in
[issue 6](https://github.com/ArtemKoval/library_crm/issues/6) carries the
turn and token counts beside it.
