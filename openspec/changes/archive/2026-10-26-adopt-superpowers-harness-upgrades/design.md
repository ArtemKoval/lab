# Design

## Context

Facts from the review round on 2026-10-23 and 2026-10-24 (adversarial author, three lenses, adversarial reviewer; four independent agents, one reconciliation):

- `obra/superpowers` at commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b` (MIT) solves the same five gaps this change targets: discipline lost on compaction, execution progress lost on long runs, no debugging procedure, no completion-claim procedure, no skill-authoring procedure.
- The Claude Code hooks reference (code.claude.com/docs/en/hooks.md) confirms: a `hooks` object keyed by event, matcher groups, per-entry `type`/`command`/`timeout` (integer seconds)/`async`/`shell`; SessionStart sources `startup|resume|clear|compact|fork`; context injection through the nested `hookSpecificOutput` object; SessionStart is not blockable; `CLAUDE_PROJECT_DIR` is exported and the command runs through `sh -c`.
- This repo has no `hooks` key in `.claude/settings.json` today. The file carries `outputStyle`, `enabledMcpjsonServers`, and three `permissions.allow` entries.
- The house tool layout nests the package (`tools/zai_routing_audit/zai_routing_audit/`). Root-suite tests import tool code through a conftest `sys.path` insert with a `MUTANT_UNDER_TEST` stand-down, so the flat mutation mirror works.
- The gate tools (pytest, pytest-cov, ruff, mutmut) live in the registered `zai-routing-audit-python-deps` venv. `devcontainer_init` already reuses that venv for its gates; reuse is the repo convention.
- The schema's tasks template mandates dotted task ids (`- [ ] X.Y`), so a brief selector that only accepted plain numbers could not read this repo's own `tasks.md`.
- The root suite is hermetic on ubuntu-24.04 with that venv: every e2e test is env-var gated, the undercover byte-identity test self-skips without a local clone, notebooks stub third-party imports, and zai tests monkeypatch the network.
- The project has CI (`build.yml`) but it only builds fde; the root suite never runs in CI.
- `openspec/config.yaml` pins six proposal/specs/design/adr/apply rules, and the contract test pins that count. The pipeline's stale text says "This repo has adopted no hooks yet" in two places.

## Goals / Non-Goals

Goals:

- Discipline that survives compaction: the charter lands in context at startup, after a clear, and after a compaction.
- Long apply runs that keep their place: a ledger, a per-task brief, and a review package that stay true when conversation memory does not.
- Fixed procedures for debugging, completion claims, and skill authoring.
- Review replies and agent dispatch that follow written rules.
- The root suite runs on every pull request.

Non-Goals:

- No install of the superpowers plugin, marketplace machinery, or its multi-harness porting layer.
- No visual companion; it reports the version to an external site.
- No port of `using-superpowers` (its invoke-before-any-reply rule fights Step 0) or of the upstream TDD and worktree skills (covered here).
- No adoption of the `diagnosing-superpowers` tooling; ADR 0003 records it as the reference design for a later change.
- No Windows support for the hook script (repo development is macOS; CI is ubuntu).
- No hook-based enforcement of the pipeline beyond the charter; the charter informs, it does not block.

## Wiring

Lightweight C4-inspired container view; ASCII, an assumption recorded here because no repo precedent fixes a diagram format. Containers are runnable units; components live inside `plan_exec`.

```
                +-------------------------------+
                |      Claude Code harness      |
                |  (settings.json, agents)      |
                +---------------+---------------+
                                | SessionStart (startup|clear|compact)
                                v
                +-------------------------------+
                |  harness-charter.sh           |   .claude/hooks/charter.md
                |  emit hookSpecificOutput      |
                +-------------------------------+
                                | additionalContext
                                v
   user <------> primary agent; dispatches: adversarial pair, senior pair,
                                general-purpose agents (model named per dispatch)
                                |
        +-----------------------+--------------------------+
        | apply run (openspec-apply-change)                  |
        v                                                    v
 +-------------------------------+            +------------------------------+
 | plan_exec CLI (stdlib)        |            | new skills                   |
 |  brief -> task-N-brief.md     |            |  systematic-debugging        |
 |  package -> review-package.md |            |  verification-before-        |
 |  ledger -> .plan_exec/ (git-  |            |    completion                |
 |    ignored scratch)           |            |  writing-skills              |
 +---------------+---------------+            +------------------------------ |
                 | reads plan + git repo (read-only)
                 v
        tasks.md, delta specs, git history
                 |
                 v
        root suite (tests/) --CI: tests.yml (ubuntu, repo venv)--> gates:
        pytest --cov plan_exec (100%), ruff C901, mutmut local
```

Boundaries: the hook only informs; plan_exec only reads the repo and writes under its `--out` directory; the skills only advise. No component blocks a session.

## Decisions

### D1. Adopt the mechanics, not the plugin

We vendor the seven mechanics (charter hook, execution tooling, three skills, pipeline rules, the reference designation) and leave the plugin, its marketplace layer, its telemetry, and its multi-harness porting out. The mechanics are small enough to own; the plugin is a second harness we would have to keep in sync.

### D2. Hook envelope and settings shape, docs-confirmed

`harness-charter.sh` emits exactly one top-level JSON object: `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": <escaped>}}`. The docs read only the nested form; upstream's comment warns that extra top-level context fields inject twice. The settings entry carries `type: command`, the quoted direct command `"$CLAUDE_PROJECT_DIR/.claude/hooks/harness-charter.sh"`, `timeout: 10`, and `async: false` (explicit, because `true` would background the injection). The script uses `#!/bin/bash`, reads the charter with the `$(<file)` builtin, resolves the charter path from `CLAUDE_PROJECT_DIR` with a `$0`-derived fallback (the cwd fallback branch exists in the script but stays unreachable through the wired command, which always carries slashes), escapes with bash parameter substitution, prints with `printf`, and exits 0 on every outcome, with a one-line fallback when the charter is missing. The charter file holds no control characters outside newline, carriage return, and tab, pinned by contract test, so the five escaped classes cover strict JSON. Mode 100755 in the commit. `resume` and `fork` stay unmatched on purpose: those sessions replay context that already holds the charter.

### D3. The charter informs; it does not restate

`charter.md` (40-60 lines) carries pointers to CLAUDE.md, the pipeline skill, and `openspec-git-discipline`, the gate names, the two-merge discipline (the house term for the proposal-before-apply and merge-before-archive gates), the skills-first rule, and the worktree rule. It carries no step prose, so it cannot become a second source of truth. The contract test pins four shared marker strings that must appear in both the charter and the pipeline skill, so drift fails the suite. The four strings, chosen because the skill already carries them verbatim: `OpenSpec`, `openspec-git-discipline`, `Nothing proceeds on red`, `adversarial-reviewer`.

### D4. plan_exec is Python, not bash, and shares the repo venv

Upstream's brief and review-package scripts are bash. This repo's gates measure Python: coverage, ruff C901, mutmut. A Python port under the house nested layout (`tools/plan_exec/plan_exec/`) makes the deliverable testable under the gates we already run. The package is stdlib-only, so it needs no dependency file and no new setup unit; the gate tools come from the registered `zai-routing-audit-python-deps` venv, the same reuse `devcontainer_init` already relies on. `cli.py` stays a thin argparse surface (Division); the parsers and ledger logic carry the branches so no function exceeds complexity 10.

### D5. The brief parser reads both task shapes

Selectors accept `N` and dotted `X.Y`. The parser handles `### Task N:` section plans and `- [ ] X.Y` checkbox plans with indented bodies, because the schema's own tasks template mandates the dotted checkbox form. A section task body runs to the next heading of the same or a shallower level. A checkbox task body runs to the next checkbox at the same indent, the next heading, or a dedented non-blank line; blank lines inside the body stay. Fenced blocks (``` or ~~~) hide their content from the stop rules. Unknown, non-numeric, or missing-file cases exit 2 with a message, never a traceback; argparse's native parse errors already exit 2. Write failures (an output path that cannot be created) also exit 2 through the same error types.

### D6. The ledger is append-only scratch with a fixed convention

`ledger` writes `<repo-root>/.plan_exec/<plan-basename-with-extension>/progress.md`, git-ignored through this change. `--dir` is optional and overrides the default. The repo root comes from `git rev-parse --show-toplevel` of the working directory, with the working directory as the fallback outside a repository. `init` is idempotent: a matching identity exits 0 and writes nothing. `show` prints the ledger content. `complete` requires `--tests` and `--result`. Appends verify the identity value, not just its presence, so an append through a wrong directory refuses. The global `--json` flag (machine-readable `{"ok", ...}` payloads) sits deliberately below the spec: it is developer ergonomics, exercised by tests, not contract. The ledger is per-run state: a run reads it again after compaction, but later work reads the durable record, which stays in `tasks.md` ticks and git history. The identity line names the absolute plan path; a foreign identity exits 2. Single-writer by design (one agent per plan), stated in the README. When the default directory is taken by another change, pass `--dir .plan_exec/<change-id>`. The upstream lesson stands behind it: controllers that lost their place re-dispatched completed tasks, the most expensive failure observed there.

`ledger` writes `<repo-root>/.plan_exec/<plan-basename-with-extension>/progress.md`, git-ignored through this change. `--dir` is optional and overrides the default. The repo root comes from `git rev-parse --show-toplevel` of the working directory, with the working directory as the fallback outside a repository. `init` is idempotent: a matching identity exits 0 and writes nothing. `show` prints the ledger content. `complete` requires `--tests` and `--result`. The ledger is per-run state: a run reads it again after compaction, but later work reads the durable record, which stays in `tasks.md` ticks and git history. The identity line names the absolute plan path; a foreign identity exits 2. Single-writer by design (one agent per plan), stated in the README. The upstream lesson stands behind it: controllers that lost their place re-dispatched completed tasks, the most expensive failure observed there.

### D7. Port policy: adapted prose, pinned provenance

The three skills are new prose in the house style (ASD-STE100), not verbatim upstream text: the upstream files carry superpowers cross-references and a different instruction register. Each SKILL.md pins `metadata.ported` in the same frontmatter shape the intent-driven ports use (`from:`, `commit:`, `license:`) with the upstream repo `obra/superpowers`, the commit `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`, and MIT. The mechanics survive the adaptation: the four debugging phases with the three-fix architecture question, the claim-command-output table, the baseline-then-write-then-close-loopholes loop, and the form-to-failure table. The provenance test is separate from the `PORTED_SKILLS` tuple, whose pinned commit differs. `verification-before-completion` states its boundary against `verify-change`: artifact verification on demand versus claim discipline during apply.

### D8. Pipeline rules land in the pipeline skill only

The five rules go into `feature-pipeline/SKILL.md` with this content: review reception (verify each finding before the fix; push back with technical reasons when it is wrong; no performative agreement; clarify every unclear item before any fix; reply in the review thread, not top-level), model selection (name the model on every agent dispatch when the harness allows it; give the final whole-diff review to the strongest available model; judge cost by turn count, not token price), the discard contract (destroy work only after the user types discard), worktree provenance (remove only worktrees this pipeline created; on a removal refusal, show the user the file list first, never force; delete the branch after the merge; leave worktrees other tools created in place), and the builder check (one fresh agent reads only the change artifacts and asks a builder's questions, sorted into answered, minor, theirs; theirs holds only what the user alone can answer, delivered in one message). `openspec/config.yaml` gains no `Must use` lines, so the pinned six-rule count holds. The two stale "no hooks yet" statements in the same file go, because deliverable A introduces the first hook and the skill must not contradict the settings file. This change dogfoods the builder check; its round settled the CLI defaults, the parser boundaries, and the rule texts recorded here.

### D9. CI runs the suite; mutation stays local

`tests.yml` triggers on pull requests, pushes to main, and manual dispatches, with `paths-ignore: ['fde/**', 'llm_ops/**']` — the suite reads most other paths (CLAUDE.md, `.claude/**`, `adr/`, `glossary/`, templates), so a narrow allowlist would under-trigger. The job sets up Python 3.12, builds the registered venv from `tools/zai_routing_audit/requirements-dev.txt`, runs pytest with `--cov plan_exec --cov-branch --cov-fail-under=100`, and runs ruff on `tools/plan_exec`. The fde ignore is safe today because the undercover byte-identity test self-skips on CI; a change that makes that test CI-capable must revisit the filter. Mutation stays a local per-change gate; a CI mutation run would cost more wall time than it protects.

### D10. Council notes and the ADR style record

The adversarial-authoring round for this proposal produced two council files (`proposal.council.md`, `design.council.md`), matching the archived precedent; the specs, tasks, and adr artifacts run under their own mandated skills, so blanket council files for them would duplicate records those skills already own. The ADR skill's `preferences.md` moves from `unset` to `custom`, recording the house format that ADR 0001 and 0002 already use and the harness spec already pins; the skill demands a record before drafting, and the repo had made the choice without recording it.

## Risks / Trade-offs

- [Every session carries about 60 extra lines] -> The charter is bounded by a test and points instead of copies. Accept.
- [The hook runs on every matching event] -> Builtin-only script, timeout 10, budget under 100 ms, measured at implementation. Accept.
- [settings.json edits can clobber keys] -> The update-config skill owns the write and the contract test asserts all existing keys survive. Accept.
- [The brief parser guesses plan formats wrong] -> Two shapes specified and tested; a third shape becomes a new selector, not a parser rewrite. Accept.
- [The ledger dir holds state outside version control] -> The durable record lives in tasks.md and git; the ledger is per-run scratch by design, stated in the README. Accept.
- [CI installs unpinned gate tools that drift from local] -> Known limitation of the shared requirements file; bounding the pins is a recorded follow-up, not this change. Accept.
- [Ports drift from upstream] -> Provenance pins the commit; the mechanics list in D7 makes future re-diffs reviewable. Accept.

## Migration Plan

1. Proposal PR merges the artifacts, ADR 0003, and the council files.
2. Implementation PR lands the hook, the tooling, the skills, the pipeline edits, and CI, under the full gates, with the ledger dogfooded on this change's own tasks.
3. Archive PR syncs the two delta specs into `openspec/specs/`.
4. Rollback: remove the `hooks` key, delete the tool and skill directories, revert the pipeline edits; no runtime project depends on any of it.

## Open Questions

- None. The user approved all seven mechanics on 2026-10-23. The review round returned no open question that changes product intent; the two implementation-time verifications (live hook fire, hook runtime) are tasks, not open decisions.
