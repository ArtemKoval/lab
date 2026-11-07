# Analysis: dsh-superagent — what this lab can port

- Issue: ArtemKoval/lab#103
- Source: https://github.com/deepseek-ai/dsh-superagent-prototype, MIT, at
  commit 8c32a9d (one commit, "research prototype")
- Date: 2026-11-07
- Status: analysis only. The proposals in section 6 need approval. Each
  proposal becomes a separate change with its own review through the feature
  pipeline.

## 1. Scope

This run examines dsh-superagent and maps its agentic tooling to the harness
surfaces in this repository. This run does not change any skill, hook, or
tool. Section 3 names the mechanisms this lab already covers. Section 5
lists the candidates this run defers, with reasons. Section 6 lists the
proposals in value-versus-effort order. The user selects the proposals to
build. Each build is a separate change with its own review and gates.

## 2. What dsh-superagent is

dsh-superagent is a proactive coding agent for one GitHub repository,
packaged as a bundle for the DeepSeek Harness. It listens to GitHub and,
optionally, Feishu. An allowed person asks for work in a conversation. The
agent opens a work item, runs it in its own agent session and directory, and
answers in the original conversation, usually with a pull request. A web
panel shows what needs a person. The scale is about 25,000 lines of
TypeScript. The README carries a research-prototype disclaimer, so this run
treats every mechanism as unproven until its code confirms it.

The core principle: take as little human attention as possible, and give as
much value as possible. The agent acts only when a person asks, or when a
rule the team wrote allows it. It speaks only when a person must act, or
when a person can use a result.

The disciplines that matter for this lab:

1. **Two-layer evaluation.** A deterministic gate decides who may start
   work and with what strength. A model assessment judges only the
   candidates that pass the gate. Facts stay in code: prompt text cannot
   change the gate, the mandates, or the admission rules.
2. **Strength levels and accept modes.** An allowed person who addresses
   the agent makes an explicit request. Every other human message makes at
   most an inferred candidate, and a bot never makes more. A candidate
   needs an assessment. The accept mode decides what an assessment can do:
   `off` accepts nothing, `observe` records what it would accept, and `auto`
   accepts. Default is `observe`.
3. **Mandates and policy versions.** An accept grants an immutable mandate
   that records the policy version, the scope, the strength, and the
   matched rules. Only a person's stop withdraws it. A resume revalidates
   the mandate against the current policy before it wakes the work.
4. **Structured reports and derived stages.** A worker reports one of
   `progress`, `waiting`, `ready`, `blocked`, `failed`, `dropped`. Each
   ticket stage derives from the stored reports and inputs, and the first
   matching row of a fixed table wins. A question for a person travels
   through a structured field, never through free text.
5. **Stored work.** Every external write — a relay, a delivery, a channel
   message — is stored first and done after the state change commits. A
   failed write retries with backoff. Messages of one ticket to one
   conversation keep their order. A dropped message keeps its record, so
   nothing queues twice.
6. **Honest, quiet communication.** One concrete acknowledgement per
   request, in the form "On it: <object and expected result>". Default
   silence while work runs. One sentence per result. A review thread whose
   finding is fixed and verified resolves silently, and a declined
   suggestion gets one sentence in its thread. A draft is marked unfinished.
   An automated reviewer gets at most three review rounds per pull request,
   across restarts.
7. **Idempotency, locks, and recovery.** Every identifier derives from its
   content through a SHA-256 hash (`src/core/ids.ts`), so a re-poll or a
   retry produces the same id and changes nothing. A duplicate accept of
   one trigger is refused with the reason `startedTicket`. The runtime
   takes a lock on the state directory before it opens its store
   (`src/app/runtime.ts`, stale after 30 seconds), so a second instance
   cannot start. A restart gives each interrupted assignment a recovery
   note: examine the directory, the git history, and GitHub before you
   repeat any outside action.
8. **Self-repair with silence on health.** An hourly task in the
   operator's own profile runs the status script. Exit 0 says nothing.
   Exit 1 restarts the agent, unless a stop marker stands. Exit 2 or 3
   reports the errors or the setup problem to the operator.

## 3. What this lab already covers

The two systems agree on several designs. These mechanisms need no port:

| dsh-superagent | This lab |
| --- | --- |
| Explicit intake, and `observe` before `auto` | The loop works on operator-filed issues as a practice, not as a gate. P3 adds the gate. The human spec gate sits between propose and apply |
| Pause processing, and the stop marker that `--respect-stop` keeps | The `.claude/halt` file. The halt gate denies model-backed calls while it stands |
| A `blocked` report, and a structured question for a person | The `blocked` label, and the structured reason comment on the issue |
| Idempotency by stable keys, and a restart recovery note | Labels carry the loop state, and `Refs #NN` links a PR to its issue. The scan derives `resume` and `repair` from stored facts |
| Outside text stays data, and never changes rules | The apply fold keeps loop comments out. The gate-integrity guard protects the gate paths |
| The three-round cap per automated reviewer | The inner loop allows at most 2 refinement rounds, each driven by a new external signal |
| A PR merely existing is not a delivery milestone | The `verification-before-completion` skill, and the proof line in every commit and PR |
| Panel principles: a count equals its list, quiet by default | `cc_logging`, the handover telemetry, and the residue scan |

## 4. Mechanisms this run examined in detail

- **Intake and admission.** A source translates each event into one
  immutable trigger with an actor, a strength hint, and channel addresses
  (`src/sources/github-trigger.ts`). An edit produces a new trigger id
  through the edit version, while a re-poll reproduces the same id. The
  gate examines the sender against the source's allowed list, its bot
  list, and its admission table (`src/policy.ts`, `src/admission.ts`). The
  admission table gives each receiving scope its own cells, so a team can
  let an unlisted person in one chat ask for work while every other
  unlisted sender stays out. A bot login, a `[bot]` suffix, never passes
  the gate as a person.
- **Durable effects.** All external work sits in one SQLite effect queue
  (`src/app/effects.ts`). One row per kind and key: a newer payload
  replaces an older one, the queue position stays, and dispatch happens
  only after the state change commits. A transient "not now" defers
  without a failure mark. Three consecutive real failures turn the kind's
  health entry to `error`. The outbound channel keeps permanent receipts.
  A later message of one ticket to one conversation waits behind its
  earlier unresolved one (`src/app/outbox.ts`).
- **Send reconciliation.** A GitHub comment embeds a marker with its
  message id. Before it posts, the channel scans the existing comments for
  the marker, and a found marker means already sent
  (`src/sources/github-channel.ts`). A send whose outcome is unknown is
  therefore safe to retry.
- **Execution isolation.** Each ticket gets one executor session and one
  directory, prepared by a fixed command with a ten-minute limit. A failed
  prepare command never retries automatically, because "an existing
  directory counts as prepared" would trust whatever the failed command
  left behind. A retry or a person's message tries the preparation again.
  A worker slot limit bounds concurrency, and one extra slot stays
  reserved for a person's message, so new work cannot starve a person's
  follow-up (`src/executor/dsh.ts`).
- **Failure routes.** A passing failure — HTTP 408, 429, 5xx, and a
  connection-error list — retries three times with a backoff that starts
  at 15 seconds. A failed prepare command does not retry automatically. A
  source read failure stays on its thread, and a thread whose reads keep
  failing drops one day later, with its read position intact. HTTP 404
  retries, because it can mean revoked access, and HTTP 410 drops, because
  the target is gone. A channel message drops only when the conversation
  is gone or the source no longer listens there, and its record stays.
- **Derived stages.** The stage table puts every person-blocking stage
  above every working stage, so an overview that reads the table top-down
  answers "does anything need me" first (`src/core/stage.ts`). The latest
  report `blocked` or `failed` holds the automatic inputs, while a
  person's message still flows to the worker.
- **Environment hygiene.** Worker shells run through CLI shims and a
  scrubbed environment: token variables unset, host git variables unset,
  a worker git config that never guesses an identity, blocked commands
  shimmed to fail, and a verify step that rejects a ticket repository
  whose own git config carries credential settings
  (`src/infra/environment.ts`). The doc names the limit honestly: these
  are defaults, not a security boundary.
- **Noise control with budgets.** Messages carry word budgets, 100 for a
  chat message and 30 for a routing note, and a guard refuses overlong
  text with a rewrite instruction (`src/infra/text.ts`). The reply gate
  admits only the purposes answer, result, and attention, and refuses
  progress. Newer unsent notices with the same name replace the waiting
  one (`src/app/notices.ts`).
- **Setup as an interview.** `SETUP.md` runs a probe first, asks one
  question per message with a recommended answer, collects every answer
  before it executes, sends one plan message, and puts every hands-on step
  with secrets into one operator message with exact commands.

## 5. Candidates this run defers, with reasons

- **The full trigger-engine for proactive rules.** The observe and accept
  modes govern work nobody asked for. This lab produces no recurring signal
  volume that justifies a rule engine today. The scheduled runner in P2
  produces the evidence that decides this later.
- **Reviewer-credit commit rewriting.** dsh rewrites a PR branch so each
  commit carries a `Co-authored-by` trailer per reviewer. The rewrite is
  risky, and this repo squash-merges, so per-commit trailers do not
  survive.
- **Prompt-override machinery with base tracking.** dsh versions prompt
  parts and diffs a changed default against a team override. Git history
  serves this for this repo's skills.
- **A web panel.** The dsh panel answers three questions in one place.
  Open issues, the reports directory, and the handover issues carry the
  same answers here.
- **Feishu sources, worker-slot concurrency, and background-job limits.**
  One loop runs one issue at a time on one host, so these mechanisms have
  no workload to govern.
- **Policy-version revocation machinery.** The spec gate and the ADR
  directory carry durable rule changes with their own review.
- **Agent memory across runs.** dsh-superagent has no dedicated memory
  feature, and that is a finding, not a gap. A worker carries its
  workspace directory, its git history, its persisted session history,
  and the recovery note. The lab's memory directory and handover issues
  already carry more.

## 6. Proposals

Order: value against effort.

### P1. A lock and hold check for the loop pre-flight — high value, low effort

dsh locks its state directory, so a second instance cannot corrupt state.
The process-issues skill says: "Run one loop invocation at a time. No lock
mechanism enforces the rule, so the operator carries it." Two sessions can
work the same issue today.

- Change: `tools/process_issues` gains a lock examination. A lock file at a
  stable path holds the holder's process id and start time. The scan exits
  2 with the holder's details when the lock is fresh, and reports a stale
  lock it can clear when the process no longer runs. dsh takes its state
  lock with a 30-second stale time before it opens its store, and its
  service script refuses a duplicate through a pid file, a process scan,
  and a probe. The skill pre-flight gains one step for the lock, and one
  step that stops the run when the `.claude/halt` file stands.
- ASIT: Unification. The scan CLI owns the pre-flight state, and the
  peak-hours gate command is the existing pattern for a pre-flight step.

### P2. A scheduled loop run with a status contract — high value, medium effort

dsh runs an hourly task that repairs the agent when it stops, and stays
silent when all is well. The lab loop advances only when the operator asks.
An approved issue waits for an operator prompt to enter apply.

- Change: `tools/process_issues` gains a `status` subcommand with the dsh
  four-level contract (`scripts/dsh-superagent`): exit 0 running, exit 1
  stopped or restartable, exit 2 running with a component error, exit 3
  running and waiting for setup. The dsh doc draws the line that matters:
  a restart fixes neither 2 nor 3. The process-issues skill gains a
  scheduled-run recipe: run the scan, apply the oldest actionable issue,
  stop at the spec gate, and report only exceptions. The schedule sits
  outside the peak window, and the peak-hours gate stays as the backstop.
  The halt file stays the intentional stop, and the recipe honors it.
- Open decision for the change: Claude Code cron against a system timer.
- ASIT: Unification. The scan and the label states exist. The recipe and
  the status contract extend them.

### P3. An admission gate on the loop intake — high value, low effort

This repository is public. Any GitHub account can open an issue, and the
scan admits every open issue into the rotation, so a stranger can start
model-backed work. dsh keeps an allowed list per source. An unlisted person
gets nothing by default, and explicit strength only where an admission cell
grants it. A bot never makes an explicit request.

- Change: the scan carries an allowed-author list with the operator's
  login. An issue from an author outside the list maps to a new state that
  takes no action, and the state carries the author in the `--json`
  payload. An author whose login ends in `[bot]` never passes, even when a
  list entry names it. dsh marks the agent's own login as non-human, so
  its own messages never authorize work. The loop equivalent: an issue the
  loop's own account files takes no action either.
- Open decision for the change: the place of the new state in the
  precedence order, because a foreign-author issue can already carry a
  gate label.
- ASIT: Unification. The scanner owns admission today, and its state
  precedence gains one entry.

### P4. A write-ahead ledger for loop writes — medium value, medium effort

dsh stores each external write before it runs, retries it with backoff,
and keeps a record of what it dropped. A loop run between two commands can
lose a write: a label set, a comment posted, a merge done. The residue scan
finds some leftovers after the fact, and the `repair` action repairs the
loop comment and the state label, but nothing records the intent before
the write.

- Change: the loop phases append one ledger line before each GitHub write,
  and one after the write confirms. The `resume` and `repair` actions read
  the unconfirmed lines first. The plan_exec ledger is the existing ledger
  contract, so the change extends it or follows its form. dsh pairs its
  queue with two reconcile rules this change can adopt. A comment embeds a
  marker with its id, and a scan for the marker decides the retry. One row
  per kind and key, so a newer intent replaces an older one.
- This proposal gains its value when P2 lands, because unattended runs
  raise the cost of a lost write.
- ASIT: Unification. The plan_exec ledger gives the line format. The new
  ledger needs a store that survives across runs, which the plan_exec
  per-run scratch does not.

### P5. A communication discipline section for loop and PR traffic — medium value, low effort

The dsh team sections carry rules this lab's skills do not state. Give one
concrete acknowledgement per request, in the form "On it: <object and
expected result>". Never give a generic "I will do it". Stay silent while
work runs. A review thread whose finding is fixed and verified resolves
silently. A declined suggestion gets one sentence of reason in its own
thread. A draft is labeled unfinished. The charter already says "reply in
the review thread", and the loop comments carry the fixed
"process-issues loop" line.

- Change: a short communication section in the feature-pipeline skill,
  near the review steps, and the acknowledgement rule in the
  process-issues skill: when the loop picks up an issue, it posts one
  comment that names what it will do. dsh enforces its budgets in code:
  100 words per chat message, 30 per routing note, and a reply gate that
  refuses a progress purpose. This lab starts with the written rules, and
  a later change can add a mechanical limit if the text overruns.
- ASIT: Unification. Existing skills gain rules. No new component.

### P6. The setup interview protocol in project-setup — medium value, low effort

The dsh `SETUP.md` interview keeps the operator's attention small: run a
probe first, ask one question per message, give each question a
recommended answer and one sentence of why, collect every answer before
execution, send one plan message, and put every hands-on step with
secrets into one operator message with exact commands. The project-setup
skill examines the registry and asks for permission, but states no
interview rules.

- Change: the project-setup skill gains the interview protocol as written
  rules: probe first, one question at a time with a recommendation, one
  plan message, operator hands-on steps in one message with exact
  commands, and never ask for a secret in the chat.
- ASIT: Unification. The skill gains rules. No new component.
