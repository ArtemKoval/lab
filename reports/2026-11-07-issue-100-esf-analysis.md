# Analysis: esf — what this lab can port

- Issue: ArtemKoval/lab#100
- Source: https://github.com/mitkox/esf, MIT, at v1.0.0-rc.1 (commit e5567fb)
- Date: 2026-11-07
- Status: analysis only. The proposals in section 5 need approval. Each
  proposal becomes a separate change with its own review through the feature
  pipeline.

## 1. Scope

This run examines esf and maps its agent tooling to the harness surfaces in
this repository. This run does not change any skill, hook, or tool. Section 5
lists the proposals. The order is value against effort. The user selects the
proposals to build. Each build is a separate change with its own review and
gates.

## 2. What esf is

esf (Engineering Software Factory) is a self-hosted software factory. A task
activates a durable Change. Each run executes a coding agent in a CubeSandbox
microVM. The run verifies the patch with deterministic gates. The host
stores the patch and the evidence. Temporal coordinates the workflow. esf
began as a
fork of Machinist. The fork removed the inherited CLI, control plane, and web
UI in version 0.6.2. The scale is about 41,000 lines of Go, 1,750 lines of
Python, and a read-only operator console.

The disciplines that matter for this lab:

1. **Three outcomes.** The agent result, the verification result, and the
   factory result are separate facts. "An agent saying it succeeded is never
   enough."
2. **Deterministic verification.** Gates run as fixed argv vectors, and every
   step runs (no stop at the first failure). The output of even a passing gate
   becomes evidence. "A green build that nobody can inspect is not evidence."
3. **Gate integrity.** Before it honors anything else, the factory compares
   the hash of each gate file with the blob of that file at the baseline
   revision (`git rev-parse <baseline>:<path>` against
   `git hash-object <path>`). A diff-based comparison misses three ordinary
   git operations: assume-unchanged index flags, a committed tamper, and diff
   header rewrites. A gate that the comparison cannot decide counts as
   modified. A comparison that did not run is recorded as not run, never as
   clean.
4. **Behavior monitor.** `internal/threatmon` carries 40 named rules in 10
   categories with severities. The rules match normalized lines: ANSI escapes
   stripped, carriage returns dropped, backslash continuations joined. The
   monitor scans two inputs: the agent output and the patch. Operator rules
   add, never remove. A finding at or above the trip severity quarantines the
   run before verification.
5. **BLOCKED as a first-class outcome.** The agent writes
   `.factory/blocked.json` beside the checkout with a reason. The run ends as
   BLOCKED, and the factory records verification as SKIPPED. The factory runs
   the gate-integrity comparison before it honors the signal. The documented
   reason: an agent with no honest way to stop looks for a dishonest one.
6. **Honest evidence.** The factory records a capability the provider lacks
   as SKIPPED with a reason. An alert with no webhook counts as not
   delivered, never as delivered. The change record recomputes spend totals
   from the run manifests. The total is a floor, never an estimate.
7. **Change lineage.** A Change owns identity, and runs are activations of it
   with reasons `initial`, `rework`, `retry`, or `candidate` and a
   `parent_run_id`. A review rejection note becomes the rework note of the
   change. The factory never injects that note into the next prompt, because
   a human note is untrusted text.
8. **Operator controls.** `factory cancel`, `factory halt` (dry run by
   default), `factory threats` across runs, and the leak scan: every factory
   sandbox carries origin and run id tags, and `factory sandboxes` exits
   non-zero while a factory-tagged sandbox is alive.
9. **Redaction at the evidence boundary.** Nine regex rules mask token shapes,
   and operator-registered literal secrets mask by value, longest first.

## 3. Method

1. Clone the repository at commit e5567fb, and read the README,
   ARCHITECTURE, the factory guide, ADRs 0001, 0004, and 0007, the operator
   guide, and the harness guides.
2. Examine the Go internals for the mechanisms: the threatmon rules, the
   quarantine path, gate integrity, verification profiles, the change model,
   the inventory contract, redaction, and the leak scan.
3. Examine the Python and JavaScript tooling: the brief lab, the intake
   decision client, and the issue-triage workflow.
4. Map each mechanism to the repository surfaces, and derive the proposals.

## 4. Where the lab already follows esf

| esf idea | Lab surface |
| --- | --- |
| Named harnesses, never raw executables | The skills and agent definitions, with model pins in `tools/dspy_gate/gates.yaml` |
| Deterministic verification decides | The quality gates and the "nothing proceeds on red" rule in the feature-pipeline skill |
| The inventory is the harness contract | The charter hook injects the charter at session start, clear, and compaction |
| Evidence is durable and outside the run | `.cc_logging/`, `handover_telemetry`, and the handover issues |
| A review gate pauses the run | The process-issues human-approval states |
| Redaction at the evidence boundary | The cc-logging hook redacts at write time |
| Credential hygiene | The sec-scan skill, push protection, and the fixture-secret rule |
| Model pin re-certification | dspy-gate Gate 5 |

The gaps: gate integrity, an operator halt, a first-class blocked state,
per-gate evidence in the handover, a patch secret scan in CI, and a residue
scan. Section 5 proposes a port for each gap.

## 5. Proposals

Order: value against effort.

### P1. Gate-integrity guard for protected paths — high value, low effort

esf verifies that no run rewrote the gates that judge it. This lab has the
same shape of risk in pull requests: a change can weaken a gate in the same
pull request that uses the gate. Examples: a conftest skip, a raised crapper
threshold, a removed hook line in `.claude/settings.json`.

- Change: a guard that fails when a pull request diff touches a protected
  path set and the pull request carries no explicit acknowledgment marker.
  The default protected set: `.claude/hooks/`, the hooks wiring in
  `.claude/settings.json`, `pytest.ini`, the `tests/**/conftest.py` set,
  `tools/crapper/`, `tools/dryer/`, `tools/mutator/`, and the workflow files.
- The guard derives the changed paths from the pull request base, in the
  pattern the crm job already uses in `tests.yml`. The marker mechanism is an
  open decision for the change.
- ASIT: Unification. The changed-path derivation exists in CI. The guard adds
  one job or one root guard test, not a new framework.

### P2. A halt file for unattended loops — high value, low effort

esf gives the operator `factory cancel` and `factory halt` with a dry run by
default. An unattended loop in this lab stops only when the operator kills
the session. A kill loses the handover.

- Change: a halt file that the deny hook honors. When the file exists,
  model-backed calls get a deny with the reason from the file. The operator
  deletes the file to resume. The next loop iteration then exits cleanly and
  writes its handover.
- ASIT: Unification. The peak-hours gate is the existing PreToolUse deny hook
  with tests. The halt condition extends that hook contract, or adds one
  sibling hook if the contract split is cleaner.
- The split matters for posture: the peak-hours gate is an availability gate,
  so it fails open on a broken environment. A halt is a safety control, so it
  must fail closed.

### P3. A blocked state for the process-issues loop — medium value, low effort

esf makes "I cannot do this task" a first-class reported outcome, because
impossible tasks plus persistent agents produce out-of-bounds probing. The
loop equivalent is an issue that the loop retries without progress.

- Change: a `blocked` label and state in `tools/process_issues`. The
  process-issues skill gets the rule: when a run cannot proceed, it writes one
  structured reason comment on the issue and sets the label. The loop never
  retries a blocked issue. Only the operator clears the label.
- ASIT: Unification. The scanner already owns the states and the precedence.
  The place of `blocked` in the precedence order is an open decision for the
  change.

### P4. Per-gate evidence in the handover — medium value, low effort

esf records every gate result, keeps the output of passing gates, and draws
two lines that matter here. A gate that cannot run is a failed gate, never a
pass. A capability the environment lacks is SKIPPED with a reason, never
clean. The handover template today has a Metrics section but no gate outcome
discipline.

- Change: a Gates section in `.github/ISSUE_TEMPLATE/handover.md` with the
  rule: one line per gate, with the command, the result, and the reason for a
  skip. Extend `tests/claude_infra` to pin the section.
- Note: the issue-95 report P3 also edits this template (a Dead ends
  section). The two changes merge their template edits, or they land in
  sequence.
- ASIT: no new component.

### P5. A diff secret scan in CI — medium value, medium effort

esf scans the patch as a distinct input beside the agent output, with the
same rule set. Literal-secret matching in esf belongs to a different
mechanism: the evidence redactor masks registered secrets on write, and it
never fails a run. GitHub push protection covers known provider shapes on
this repo. It cannot know the secrets that live only in the operator
configuration.

- Change: a CI job that matches the pull request diff against candidate
  literal secrets and against the local secret-shape patterns. The literals
  travel through repository secrets, never through the repository. A finding
  fails the job. This adaptation goes past the esf precedent: esf masks
  secrets, and it does not fail on them.
- ASIT: Multiplication. The sec-scan skill already owns the pattern set. The
  CI job reuses it, and the skill stays the manual authority.

### P6. A worktree and branch residue check — medium value, medium effort

esf tags every sandbox with origin and run id, and `factory sandboxes` exits
non-zero while a factory sandbox is alive. Cleanup in the feature pipeline is
manual today, and residue recurred before (the worktree shared-ref lesson in
memory).

- Change: a stdlib CLI that lists the worktrees and local branches of this
  repository, names the ones with a merged pull request or no open pull
  request, and exits 2 on residue. A `--prune` flag does the removal after
  the review. The feature-pipeline skill names the tool in Step 13.
- ASIT: new tool, because no existing tool owns worktree state. The house
  contract applies: read-only default, exit 0 or 2, `--json`.

### Deferred

- **Advisory issue-readiness intake** (esf `tools/intake`): a typed ready,
  task type, and ambiguity score before implementation starts. The issue
  volume in this lab is low, the human spec gate covers the need, and a
  model-backed scorer needs a governed dspy-gate capability and spend.
  Revisit when the issue volume grows.
- **A brief lab for plan_exec briefs** (esf `tools/brief_lab`): score
  generated implementation briefs against run evidence (gates, cost, human
  rejection). The dspy-nightly loop is the existing learning surface. This
  needs live runs and spend. Revisit after P1 to P6 land.
- **The issue-triage workflow pattern** (esf `.github/workflows/
  issue-triage.yml`): owner-invoked model classification with a strict output
  schema, prompt truncation, an untrusted-data banner, and a separate
  validator job that applies the label. The mechanical `process_issues`
  classifier covers the need today. Reuse the guardrail pattern when a lab
  loop gains a model step.
- **The microVM, Temporal, and console machinery**: no port. The executor in
  this lab is Claude Code itself, and the enforcement surface is hooks and CI.

## 6. Non-goals

- No code change in this run. The deliverable is this report.
- No port of the esf runtime: CubeSandbox, Temporal, the console, and the sf
  turn service.
- No new ADR. The decisions happen in the separate changes that the user
  approves.

## 7. Sources

- Repository: https://github.com/mitkox/esf at v1.0.0-rc.1 (commit e5567fb)
- ADR 0007 (defense in depth), ADR 0004 (deterministic verification), and
  `docs/adr/0001-ax-inspired-resources.md` (resources and the change model)
- Issue: https://github.com/ArtemKoval/lab/issues/100
- Prior analysis: `reports/2026-11-07-issue-95-long-context-paper.md`
