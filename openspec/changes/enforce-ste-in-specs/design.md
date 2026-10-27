# Design

## Context

Facts from the proposal round on 2026-10-27: a grill-me interview, an adversarial author, an adversarial reviewer, and one reconciliation by the primary agent. No tournament ran, because the user's three answers left no architecture fork:

- `openspec/specs/` holds 11 `spec.md` files. The corpus holds long sentences, 7 uses of `provide`, and verb uses of `check`. The true census comes from the checker at implementation time.
- The house hook precedent is `.claude/hooks/harness-charter.sh`: stdlib script, root resolution through `CLAUDE_PROJECT_DIR` with a `$0` fallback, wiring under `hooks` in `.claude/settings.json`, subprocess tests in `tests/claude_infra/`.
- `PreToolUse` is blockable with exit code 2, and stderr feeds back to the model. The command runs through `sh -c`, and `CLAUDE_PROJECT_DIR` is exported.
- Nothing installs the lab tools. `tests/plan_exec/conftest.py` puts the package parent on `sys.path`. A hook that calls the CLI needs the same resolution on `PYTHONPATH`.
- `.coveragerc` omits each tool's `__main__.py`. `tests.yml` runs `--cov plan_exec --cov-branch --cov-fail-under=100` and a `plan_exec` lint step. Every tool carries a `ruff.toml` with `C901` at 10.
- ADRs 0001, 0002, and 0003 are in force and none is superseded. This design keeps every surface in `.claude/` (0002), keeps the tool stdlib and owned (0003), and ships the full artifact set (0001).

## Goals / Non-Goals

Goals:

- One rule authority: the CLI. The gate test, the hook, and a human caller run the same rules.
- Enforcement at two times: the write blocks at edit time, and the suite fails at test time.
- Violations that name their file, line, rule, and text, so a fix needs no second tool run.

Non-Goals:

- No enforcement of the full ASD-STE100 dictionary. The mechanical rule set only, per the user's decision.
- No coverage of `adr/`, `glossary/`, or the schema templates. Scope is specs and active changes only.
- No rewrite of `openspec/changes/archive/`. History stays as it landed.
- No new registry unit, dependency, or CI workflow.
- No Windows support for the hook script. Repo development is macOS, and CI is ubuntu.

## Wiring

Lightweight C4-inspired component view, in ASCII. The 2026-10-26 design records that format as its assumption, and this design follows it. One container: the checker CLI. The gate test and the hook are thin callers around it.

```
              +------------------------------------------+
              |           Claude Code harness            |
              |  PreToolUse (Write|Edit), pytest suite   |
              +---------------+------------+-------------+
                              |            |
              spec edit event |            | test run
                              v            v
   +------------------+   +---------------------------+
   | developer CLI    |   | .claude/hooks/            |
   | python -m        |   |   spec-ste-gate.sh        |
   | spec_ste_check   |   |   path filter, edit apply |
   +--------+---------+   +------------+--------------+
            |                           |
            |  PYTHONPATH=tools/spec_ste_check
            |  venv python, python3 fallback
            v                           v
        +---------------------------------------+
        |  spec_ste_check CLI (stdlib)          |
        |  rules -> violations -> report/json   |
        |  THE one rule authority               |
        +-------------------+-------------------+
                            |
             errors: exit 2 | warnings: report only
                            v
        gate test fails the suite; hook blocks the write
```

- The boundary sits at the CLI. Callers filter paths and resolve the interpreter. Only the CLI reads rules.
- The hook owns the edit reconstruction: it applies `old_string` to `new_string` on the file text from disk.
- The gate test owns scope: it passes the gate paths to the CLI and fails on the error severity.
- Assumption: `Write|Edit` covers the tools that write spec files today.

## Decisions

### D1. One checker, three callers

The rules live once, in the CLI package. The hook script holds no rules: it resolves paths and interpreters, and it calls the CLI. The gate test holds no rules: it calls the CLI over the scope. A human runs the same CLI by hand. A second rule implementation would drift within one change.

### D2. The sentence model

One rule turns text into sentences:

1. Replace fenced code blocks and code spans with one `CODE` token each.
2. Drop heading lines. Strip list markers and bold markers.
3. Split on `.`, `!`, and `?` at a line end or before whitespace. A sentence never crosses a line boundary.

The no-cross-boundary rule trades a small evasion path (a wrapped sentence) for determinism. House specs keep one sentence on one line, so the trade costs nothing today.

### D3. Procedural or descriptive

A sentence whose first word sits in the imperative verb set counts against the 20-word cap. Every other sentence counts against the 25-word cap. The verb set is a module-level constant of approved STE verbs (`run`, `start`, `add`, `use`, `examine`, and so on). A data file adds a load path for no gain.

### D4. Word counting

Split on whitespace. A hyphenated group, a number with its unit, and a `CODE` token are one word each.

### D5. The banned-word heuristic

The checker flags `perform`, `utilize`, `ensure`, and `provide` in their inflected forms. It flags `check` only when the surrounding words do not mark a noun: no determiner before it (`the check`, `a check`). Known noun phrases that the heuristic catches go into a per-rule allowlist. The implementation validates the heuristic against all 11 spec files and tunes the allowlist until the corpus passes.

### D6. Tense heuristics

A progressive tense is an auxiliary (`is`, `are`, `was`, `were`, `be`, `been`, `being`) before an `-ing` word: an error. A perfect tense is `has`, `have`, or `had` before a participle-looking word: a warning, because the pattern carries more risk of a false hit. Both rules keep allowlists for attested exceptions.

### D7. Hook mechanics

The script mirrors the charter hook root resolution. It reads the event JSON, filters to the gate paths, and builds the text after the edit:

- `Write`: scan `tool_input.content`.
- `Edit`: read the file from disk, replace `old_string` with `new_string` once, or over all matches when `replace_all` is set, and scan the result. A missing `old_string` allows the write, because the tool call fails on its own.

It exports `PYTHONPATH=$ROOT/tools/spec_ste_check` and runs the venv interpreter, with `python3` as the fallback. Errors exit 2 with the violation list on stderr. Warnings pass. A checker that cannot run fails open with a note on stderr. `timeout` is 10 seconds. The script touches two spec paths per session at most in practice, so the Python start time stays off the hot path.

### D8. CLI shape and layout

`python -m spec_ste_check <path> ... [--json]`, exit 0 or 2, in the house layout:

- `tools/spec_ste_check/spec_ste_check/` with `rules.py` (pure functions), `cli.py` (argparse and report), `__main__.py`.
- `tests/spec_ste_check/conftest.py` puts the package parent on `sys.path`.
- `tools/spec_ste_check/ruff.toml` mirrors `plan_exec`: `C901` at 10.
- `tools/spec_ste_check/pyproject.toml` carries the mutmut setup for the out-of-tree mutation run.

The violation record is `{file, line, rule, severity, text}`. Rule ids: `sentence-length`, `semicolon`, `contraction`, `banned-word`, `progressive-tense`, `perfect-tense`.

### D9. Gates and CI

`.coveragerc` gains the omit line for the new `__main__.py`. `tests.yml` adds `--cov spec_ste_check` and lints `tools/spec_ste_check`. The coverage floor stays at 100 for both packages. Mutation runs in an out-of-tree copy per the pipeline rules. The suite must pass there before the mutant run starts.

### D10. The gate test and the bootstrap

`tests/spec_ste_check/test_gate.py` walks the gate scope and fails on the first error severity, with the CLI's own report in the assert message. The scope includes this change's documents, so every implementation commit keeps them clean. The rewrite pass runs the CLI over the corpus and fixes what it reports.

## Risks / Trade-offs

- The regex heuristics carry false positives and false negatives. The allowlists hold the attested exceptions, and the 11-file corpus bounds the review.
- A sentence that wraps across lines evades the caps. House prose does not wrap today.
- The hook adds a process start to each spec write. The path filter keeps it off every other write.
- `MultiEdit` or a future write tool needs a matcher update. The wiring test pins the matcher, so the drift surfaces as a test failure.
- The perfect-tense warning teaches through reports, not through failures. That matches the user's decision.

## Migration Plan

No runtime project changes. Rollback removes the gate test, the hook group from `.claude/settings.json`, the coverage and lint additions, and the script. The rewritten spec text stays, because it is prose with the same meaning.

## Open Questions

- None that block implementation. The `check`-as-verb allowlist grows or shrinks against the corpus during implementation.
