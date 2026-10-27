# Proposal: enforce-ste-in-specs

## Why

The spec text in this repo must follow ASD-STE100, but no mechanical gate stops a violation today. The harness already runs the root suite in CI and carries one hook precedent, so this change adds the gate as small parts with tests.

## What Changes

- A stdlib CLI at `tools/spec_ste_check/` scans one path or a tree. It reports each violation with the file, the line, the rule, and the text. It exits 0 on a clean scan and 2 on errors. The `--json` flag gives machine-readable output.
- The rule set is mechanical, and it examines prose only: code, commands, paths, identifiers, and quoted text stay exempt.
- Errors: a semicolon, a contraction, a progressive tense, and a sentence over the word caps. The caps are 20 words in procedural text and 25 words in descriptive text. The banned words are the five that CLAUDE.md names: `perform`, `utilize`, `ensure`, `provide`, and `check` as a verb. A perfect tense is a warning, and warnings never fail the gate. The design defines the sentence model and the classification of a sentence as procedural or descriptive.
- The gate scope is `openspec/specs/**` and the active directories under `openspec/changes/**`. The checker skips `openspec/changes/archive/`.
- A pytest test runs the CLI over the gate scope and fails the root suite on an error. The `tests` workflow already runs the suite on pull requests, so the gate is in CI with no new workflow.
- The suite command adds `--cov spec_ste_check`, and `.coveragerc` omits the CLI entry point, to keep the 100 percent branch coverage floor. A `ruff.toml` in the tool joins the lint step.
- A PreToolUse hook matches the `Write` and `Edit` tools. The script `.claude/hooks/spec-ste-gate.sh` filters to the gate paths and runs the CLI on the text after the edit. The script puts the package parent on `PYTHONPATH` and calls the shared venv interpreter, with `python3` as the fallback.
- The hook blocks a write on an error and names the violations on stderr. A warning does not block. If the checker cannot run, the hook allows the write (fail-open). `.claude/settings.json` gains the `PreToolUse` group in the pattern of the `SessionStart` charter hook.
- A rewrite pass fixes every error the checker reports in the gate scope: the 11 files under `openspec/specs/` and this change's own documents. The gate covers the change documents from the first implementation commit. The fixes change words only, not behavior.

## Capabilities

### New Capabilities

- `spec-ste-enforcement`: the mechanical ASD-STE100 gate for spec text. It covers the checker CLI contract, the rule set, the pytest gate, and the write-time hook behavior.

### Modified Capabilities

- `intent-driven-harness`: the CI requirement extends its coverage floor and lint gate to `spec_ste_check`. The harness wires a second hook group for the STE gate in `.claude/settings.json`.

## Impact

- New files: the `tools/spec_ste_check/` package with a README and a `ruff.toml`. `tests/spec_ste_check/` carries a `conftest.py` that puts the package parent on the test path. The hook script `.claude/hooks/spec-ste-gate.sh` gets a subprocess test at `tests/claude_infra/test_spec_ste_hook.py`.
- Edited files: `.claude/settings.json`, `.coveragerc`, `.github/workflows/tests.yml`, and the `spec.md` files that the rewrite pass touches.
- Commands: `python -m spec_ste_check <path> [--json]`. The gate test and the hook call the same CLI, so the repo has one rule authority.
- Dependencies: none. The CLI uses the standard library only. The suite runs with the shared repository venv. No new unit in `tools/project_setup/registry.json`.
- Systems: the `tests` workflow runs the gate on the pull requests it already covers. Every `Write` or `Edit` in Claude Code runs the hook first, and the script filters to the gate paths.
- No change to the runtime projects (`fde`, `llm_ops/eval`, `notebooks`).
