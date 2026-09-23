---
name: feature-pipeline
description: Full delivery pipeline for ANY prompt that asks to build, add, implement, fix, refactor, automate, or change something in this repository — isolated branch, spec capture with OpenSpec, ASIT-guided design, standalone code, unit tests at maximum coverage, cyclomatic complexity ≤ 10, mutation score ≥ 95%, Claude tool and skill, docs, adversarial pull/merge-request review, merge, and cleanup, on any version control system. Invoke for every request that changes repository files; skip only for purely informational questions that change nothing.
---

# Feature delivery pipeline

Take any repository change from prompt to merged review. Every step is mandatory
unless it genuinely doesn't apply (a docs-only task has no MCP tool); when
skipping one, say which and why.

## Cross-cutting rules

Stated once, here: they govern every step, including steps added later — never
copy them into individual steps.

### Inner loop — plan, review, implement, review

Every step that makes a design decision or builds an artifact (code, tests,
config, hook, docs) runs:

1. **Plan** — approach, files, shape, edge cases, failure modes; run the ASIT
   pass before adding anything.
2. **Review the plan** — consult prior lessons first (`MEMORY.md`/memories,
   CLAUDE.md invariants, recent reflections), then critique against the
   requirement, CLAUDE.md, and reality; fix. Escalate with risk: independent
   adversarial review (Step 12 machinery) for a risky step; a decision
   tournament (several independent attempts, judged and synthesized) for a
   genuine fork (several valid architectures, ambiguous requirements,
   high-risk draft); an evolutionary or iterative search when a runnable
   numeric eval exists and the search space is large. Use the matching skill
   (`decision-tournament`, `evolutionary-optimization`, `session-reflection`)
   when this session's skill listing offers it; otherwise run the pattern
   inline. Surface directions that are the user's call (ExitPlanMode).
3. **Implement** the corrected plan.
4. **Review the result** — run it, read the diff, check the gates; fix. At most
   2 refinement rounds, each driven by a new external signal (failing test,
   review finding, measured regression) — iterating without one degrades output
   (Huang et al. 2023).

Scale ceremony to risk: most steps need one critique, not a tournament;
mechanical ones (branching, typo fixes) need only a sanity check.

### ASIT — solve inside the closed world

Apply ASIT (Advanced Systematic Inventive Thinking) to every problem — design,
code generation, bug fixes, review findings, harness fixes. Solutions built from
what already exists keep entropy and complexity bounded.

- **Closed World** — list the problem world (components in the system and its
  immediate environment) and solve by reorganizing it; add no new *kind* of
  component. A genuinely new module, class, public API, dependency, service,
  config key, flag, hook, or skill needs a plan line saying why no tool below
  avoided it.
- **Qualitative Change** — name the main problem factor (the variable driving
  the undesired effect). Prefer solutions insensitive to it, or that turn it
  into a benefit, over ones that merely dampen it (retries, sleeps, longer
  timeouts, special cases).

| Tool | Move | In code |
|---|---|---|
| 1. **Unification** | Assign a new use to an existing component | Give an existing function, type, registry, table, or hook the new job |
| 2. **Multiplication** | Add a slightly modified copy of an existing object | Another instance, config, pack, or interface implementation — parameterized, never copy-pasted |
| 3. **Division** | Divide an object and reorganize its parts | Split a function over complexity 10; separate pure logic from I/O; reorder or re-time steps |
| 4. **Breaking Symmetry** | Make a symmetric situation asymmetric | Common-case fast path plus explicit rare path; distinct handling at trust boundaries, for reads vs. writes |
| 5. **Object Removal** | Remove an object; assign its action to an existing one | Delete a wrapper, layer, flag, cache, or dependency; let an existing component do its job |

Prefer removing or reusing (5, 1) over restructuring (3, 4) over adding (2); a
brand-new component comes last. Small steps just ask "can something existing do
this, or can something go?"; substantial ones walk all five tools. In review,
any new component without a plan justification is removed or unified.

### Quality gates — every change touching code, hook scripts included

- **Unit tests, always**, for every new or changed function, method, and class.
  Target 100% line + branch coverage of new and changed code; exclude lines only
  explicitly, with an inline reason. Total coverage never drops — ratchet the
  configured floor (e.g. `fail_under`) up to each new total.
- **Cyclomatic complexity ≤ 10** for every function added or modified, enforced
  by a checker (e.g. ruff `C901` with `max-complexity = 10`, xenon
  `--max-absolute B`, lizard `-C 10`, ESLint `complexity: ["error", 10]`). A
  touched legacy function above 10 is split (Division) in the same change, or
  listed as a follow-up if that's unsafe in scope.
- **Mutation score ≥ 95%** on added or modified code — diff-scoped where the
  tool allows, else per touched module (e.g. mutmut, cosmic-ray, Stryker, PIT,
  cargo-mutants). Timeouts count as killed; an equivalent mutant is excluded
  only with a written per-mutant reason, never by loosening tool config. Each
  survivor is a missing assertion: add tests until it dies. Pre-existing
  survivors outside the diff become follow-ups; the project-wide score only
  ratchets up.
- **Mutate a copy, never the repo.** The suite imports in-tree source (pyproject
  `pythonpath`), so run mutants in an out-of-tree copy (`tools/`, `tests/`,
  `pyproject.toml`) and never add temp tests under the repo's `tests/`. The
  unmutated copy must pass first (else every mutant falsely "dies"); a run that
  kills nothing usually means the tests can't see the mutants.
- **Missing tooling is part of the job**: introduce any absent gate in this
  change — config, setup registration (Step 8), and a CI job if the project has
  CI.

## Step 0 — Qualify and clarify

- Purely informational (nothing in the repo changes)? Answer directly; skip the
  pipeline.
- Underspecified in a way that changes what you build (purpose, mechanism,
  interface)? Ask 1–3 concrete questions (AskUserQuestion) before coding; never
  fabricate requirements.
- Read CLAUDE.md first — the source of truth for conventions.
- Detect the VCS and review platform; use their native commands throughout.

## Step 0.5 — Placement: core or pack?

Parts of this repo are a stable **core** plus registry-loaded **packs** ("add a
pack, never edit the core"). A change belongs in exactly one; state the verdict.

Seams (registry + base contract + sibling units): a registry file (e.g. an
`__init__.py` exporting a mapping, or a JSON/YAML config list) plus a base
contract (a shared interface every entry implements) plus sibling units that
plug into it. This repo (`lab`) is a personal collection of standalone
projects (`apple/fm/`, `configs/`, …) with no such registry today — plain
core/tool code; go to Step 1. If a split ever forms here, name its actual
registry/base-contract/sibling-unit files in this section instead of this
paragraph.

Verdicts:
- **Pack** — one domain, plugin, or tenant (intent, crew, prompt, corpus, new
  vertical): the pack plus its one registry line; the core flow stays
  untouched. A pack that needs a core edit reveals a missing extension point —
  add the seam, not a special case.
- **Core** — cross-cutting (flow/router, tenancy, memory, guardrails, channels,
  the pack contract). Packs stay interchangeable: no pack name in core code.
- **New seam** — pack-specific with no clean host: a core extension point plus
  the pack using it. Interface change → ask (Step 0); two defensible,
  costly-to-reverse seams → `decision-tournament`.

Downstream: a pack depends only on the core's public contract, never on another
pack (Step 2); a pack change tests the pack in isolation plus the registry
invariant, a core change proves every pack still works (Step 3); a new pack
needs its registry line and any per-pack resources pinned by a hermetic test
that asserts the registry contains exactly the expected pack entries (Step 8).

## Step 0.6 — Surface: is it a Claude Code hook?

A **hook** runs deterministically on a harness event; a skill or MCP tool runs
only when the model chooses to. Recurring automation ("each time / whenever /
before / after X", "automatically run / block / inject Y when Z") is a hook — a
skill saying "always do X" is a wish; a hook enforces it.

- **Events** include `PreToolUse`, `PostToolUse`, `PostToolUseFailure`,
  `UserPromptSubmit`, `PermissionRequest`, `SessionStart`/`SessionEnd`,
  `SubagentStart`/`SubagentStop`, `Stop`, `Setup`, `Notification`,
  `FileChanged`, `PreCompact`, `WorktreeCreate`, and more. The set evolves:
  confirm it via the `update-config` skill or the hooks docs, then pick the
  event that fires exactly when the behavior should run.
- **Config** — `hooks` in `.claude/settings.json` (project, committed; user
  `~/.claude/settings.json` and uncommitted `.claude/settings.local.json` merge
  in), as matcher groups per event, written through the `update-config` skill,
  which owns `settings.json`. A hook reads a JSON event on stdin; exit 2 blocks
  a blockable event (or JSON stdout sets `decision`, `permissionDecision`,
  `updatedInput`, `additionalContext`), exit 0 allows, other codes are
  non-blocking errors. This repo has adopted no hooks yet
  (`.claude/settings.json` sets only `outputStyle`); Step 14's `cc_logging`
  hook is a target design, not a shipped one — confirm what actually exists
  before relying on it.

For a hook deliverable:
- Its script is standalone code — Steps 2–3 and the gates apply. Use a
  cross-platform command or the host's shell (PowerShell on Windows here).
  Hooks aren't gated by `permissions.allow`, so no `Bash(...)`/`PowerShell(...)`
  twin is needed.
- Steps 4–5 usually don't apply; say so and skip them.
- Trigger the event and watch the hook fire (and block, if it blocks); a hook
  that never fires is silently useless.
- It runs on every matching event, so budget it: time it on add/change; keep
  frequent hooks lean (stdlib; no heavy imports, network, or large I/O); set a
  `timeout`; track its runtime the way `cc_logging` records its own `hook_ms`
  (Step 14's slow-hook signal).
- VCS hooks (e.g. pre-commit) fire on VCS events, not agent events; the two
  coexist.

## Step 1 — Branch

Never work on the mainline. Sync it, then isolate the change on a type-prefixed
branch — or the VCS's nearest equivalent (bookmark, topic, stream, shelved
changelist): `<feat|fix|test|chore>/<short-task-name>`.

## Step 1.5 — Spec (OpenSpec)

Decide whether the change needs a spec, and say why. It does for new or changed
behavior visible outside one unit (CLI/MCP/API output, pack behavior,
contracts), a new pack or seam (Step 0.5), or a request that needed clarifying
questions. It doesn't for fixes restoring intended behavior,
behavior-preserving refactors, docs, dependency bumps, or harness-only changes.
- Run `/opsx:propose` on the branch and get the user's approval (ExitPlanMode)
  before writing code. `tasks.md` drives Steps 2–8 (tick each task as it
  lands); `design.md` records the plan review and any tournament outcome.
- Let specs accrete per capability as changes touch them; don't back-fill.
- No `openspec/` yet? Adopt it first as its own change: install the OpenSpec
  CLI (README's link has instructions — a clean clone does not get it for
  free), run `openspec init`, plus setup registration (Step 8). If
  `tools/project_setup/registry.json` doesn't exist yet either, stand up the
  minimal registry in that same change rather than blocking on a step with no
  prior adopter.

## Step 2 — Standalone code

The core deliverable runs without Claude Code or any LLM.
- Placement per Step 0.5, else CLAUDE.md's Layout: application code in
  `backend/` or `frontend/`; tooling in `tools/<task_name>/` (snake_case) with a
  module and CLI (`argparse`, `--json` for machine output, exit 0 on success /
  2 on operational failure).
- `tools/` code depends only on `tools/<task_name>/requirements.txt`, never on
  the `mcp` package (wrapper only); application code follows CLAUDE.md's
  backend/frontend dependency setup.
- Non-destructive by default; destructive operations need an explicit flag.
- Run it against reality before moving on — untested code is not done.

## Step 3 — Tests

Per CLAUDE.md's Testing policy, cover every applicable level — **unit
(always)**, contract, functional, e2e — under `tests/`, mirroring the source
area (`tests/access_audit/` for `tools/access_audit/`, `tests/backend/...` for
backend code), and meet the gates.
- The default `pytest` run stays hermetic: externals faked in
  `tests/conftest.py`, no network.
- e2e tests are marked `e2e` and env-var gated — opt-in only.
- Assert on behavior and outputs, not on mocks echoing their configuration.
- Each spec scenario (Step 1.5) gets at least one test.

## Step 4 — Claude tool

Expose the core as an MCP tool (for application features, only when a
Claude-facing capability is genuinely exposed):
- `tools/<task_name>/mcp_server.py` — a thin FastMCP wrapper importing the
  core, with no logic of its own.
- Register it in `.mcp.json`; add the server to `enabledMcpjsonServers` and the
  tool to `permissions.allow` in `.claude/settings.json`, mirroring any
  `Bash(...)` fallback rule with a `PowerShell(...)` twin.

## Step 5 — Claude skill (or agent)

Add `.claude/skills/<task-name>/SKILL.md` (kebab-case directory; `name` =
directory; trigger-rich single-line `description`) covering when to call the
MCP tool, the CLI fallback, and how to read results. Use a subagent definition
only for a long-running autonomous role.

## Step 6 — README.md

What it does, why, exact commands. No aspirational claims; mark gaps TBD.

## Step 7 — CLAUDE.md

Update for new commands, conventions, layout entries, or AI-facing surfaces.
Verify, don't assume.

## Step 8 — Other infra and setup

- Permissions, hooks, ignore-file entries for new artifact types. Check the
  working copy (ignored and untracked files too) for strays such as pip-version
  artifacts; never commit them.
- Anything a clean clone needs (dependency file, system tool, VCS hook,
  environment step, gate tool) is registered in
  `tools/project_setup/registry.json` and reflected in
  `.claude/skills/project-setup/SKILL.md`. A new setup doctor
  (`tools/<name>_setup/<name>_setup.py`) follows the house contract: read-only
  check by default, `--install`, `--json` with an `ok` field, `--repo-root`,
  exit 0/2; the completeness test in `tests/project_setup/` fails until it is
  registered.

## Step 9 — Run tests and gates

```bash
python -m pytest                    # full hermetic suite, must be green
python -m pytest tests/claude_infra # Claude-infra contract tests
```

Run e2e when the task has it and credentials exist
(`<GATE_VAR>=... pytest -m e2e`). Then all three gates: branch coverage (e.g.
`pytest --cov --cov-branch`), the complexity checker, the mutation run — plus
`openspec validate <change>` when Step 1.5 opened one. Nothing proceeds on red.

## Step 10 — Commit and publish

Conventional Commit subject; body with what and why; the attribution trailer
per CLAUDE.md's Commits convention (the exact one your harness specifies —
never copy a model name from older commits). Confirm the staged set is exactly
what you intend, then publish the branch (push, shelve, or equivalent).

## Step 11 — Review request

Open a pull request, merge request, or equivalent (e.g. a Gerrit change) against
the mainline: summary, mechanism, file list, a test plan of what actually ran
(commands, observed results, coverage, peak complexity, mutation score), and the
Claude Code attribution line. No review platform? Run Step 12 on the local diff
and record its outcome in the integration commit.

## Step 12 — Adversarial review, then fix

- Multi-agent review of the diff (Workflow tool when available, `/code-review`
  otherwise): correctness, config/infra validity, the guarantees the code claims
  (standalone, non-destructive, hermetic tests), doc-vs-code consistency, spec
  conformance (every scenario tested, nothing beyond the delta), the gates, and
  entropy (every new component justified by the ASIT pass). Verify each raw
  finding with independent skeptics before accepting it.
- Fix every confirmed finding; skip rejected taste-only ones. Re-run the suite
  and gates, including former survivors to prove them killed; commit and
  publish the fixes before merging.
- Check the working copy for residue; restore any file a review agent touched.

## Step 13 — Merge and clean up

If Step 1.5 opened a change, archive it (`/opsx:archive`) as the last commit,
so the mainline gets code and specs together. Merge through the review platform
(or integrate locally if there is none), squashing where the project allows,
subject `<type>: <summary> (<review ref>)`. Delete the branch locally and
remotely; resync the mainline, pruning stale remote references. Verify: request
merged, only the mainline remains, suite and gates pass on the merged mainline,
the shipped command or tool still runs. Report what was built, what review
found, gate results, and anything the user should know (new dependencies,
deliberate follow-ups).

## Step 14 — Close the loop

Each run is one turn of a loop that improves the harness (Claude Code, skills,
tools, hooks, permissions) from a mechanical signal (logs) and a narrative one
(reflection). None of this step's tooling is adopted in this repo yet — no
`hooks` key in `.claude/settings.json`, no log-analysis tool, no reflection
skill. Treat the sub-steps below as the target design: skip each one until its
tooling exists, and adopt it via Step 8, as its own change, before relying on
it.
- **Log** — once adopted, a `cc_logging` hook (or equivalent) records every
  tool call and run boundary to a local, uncommitted log; it always exits 0
  and redacts secrets at write time, so it can't break a session or leak one.
  Confirm wiring with its setup doctor, itself a project-setup unit.
- **Analyse** — when a pattern is worth chasing (not every change) and a log
  analysis tool exists, run it. Rank permission-friction (prompted or denied
  calls), recurring-error, repeated-command (work a helper or hook could
  absorb), and slow-hook signals.
- **Reflect** — after a substantial delivery, if a reflection skill exists,
  run it for what counts miss: an undocumented convention, a fix that took
  several attempts, a misleading CLAUDE.md claim, a tournament winner that
  didn't hold. Shared lessons → this pipeline (committed), local → memory,
  mechanical → the analysis. Act once the same friction recurs (~3+
  reflections); lessons pay off only when consulted (inner-loop step 2).
- **Improve** — feed findings back through this pipeline, placed via Steps
  0.5/0.6 and solved ASIT-first (extend an existing skill, hook, or rule before
  adding one): permission-friction → scoped allow-rule (+ PowerShell twin) or a
  hook via `update-config`; recurring-error → a fix or guarding hook;
  repeated-command → helper, skill, or hook; slow-hook → trim it (fewer imports,
  less I/O), move work off the hot path, or drop it. Ship with a feature's
  rigor — the value is in acting on findings, not collecting logs.