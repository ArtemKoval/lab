# Tasks: enforce-ste-in-specs

## 1. The checker CLI

- [ ] 1.1 Write `tests/spec_ste_check/conftest.py` on the `plan_exec` pattern, with the `MUTANT_UNDER_TEST` stand-down.
- [ ] 1.2 Write `tools/spec_ste_check/spec_ste_check/rules.py` with the sentence model, the word count, and the six rules; unit tests cover every rule, the caps, the exemptions, and the allowlists at full branch coverage.
- [ ] 1.3 Write `tools/spec_ste_check/spec_ste_check/cli.py` with `argparse`, the tree walk, the report, and `--json`; unit tests cover the exit codes and both output forms.
- [ ] 1.4 Add `tools/spec_ste_check/spec_ste_check/__main__.py`, `tools/spec_ste_check/ruff.toml`, and `tools/spec_ste_check/pyproject.toml` with the mutmut setup.
- [ ] 1.5 Write `tools/spec_ste_check/README.md` with what the tool does and the exact commands.

## 2. The gates and the hook

- [ ] 2.1 Write `tests/spec_ste_check/test_gate.py`, the gate test that runs the CLI over the gate scope and fails on an error.
- [ ] 2.2 Add the `.coveragerc` omit line for the new `__main__.py`, and extend the `tests.yml` suite command with `--cov spec_ste_check` and the lint step with `tools/spec_ste_check`.
- [ ] 2.3 Write `.claude/hooks/spec-ste-gate.sh` on the charter hook pattern: root resolution, path filter, edit reconstruction, interpreter fallback, fail-open.
- [ ] 2.4 Wire the `PreToolUse` group into `.claude/settings.json`, and update `tests/claude_infra/test_harness_charter.py` only where it pins the keys this change touches.
- [ ] 2.5 Write `tests/claude_infra/test_spec_ste_hook.py`: wiring, a blocked write, a warning pass, an archive pass, and the fail-open path through subprocess runs.

## 3. The rewrite pass and the corpus

- [ ] 3.1 Run the CLI over the gate scope, fix every error it reports in the 11 spec files and in this change's documents, and make the corpus pass the gate test.
- [ ] 3.2 Examine every `check`-as-verb hit by hand and tune the allowlist until the corpus holds no false hits.

## 4. The durable record and the gates

- [ ] 4.1 Write `adr/0004-enforce-ste-in-specs.md` in the house format of `adr/0001`.
- [ ] 4.2 Run the full suite, the branch-coverage gate, the complexity checker, and the out-of-tree mutation run; add tests until the mutation score reaches 95 percent on the new code.
- [ ] 4.3 Update CLAUDE.md: the tools list gains the checker, and the Specs section names the gate.
- [ ] 4.4 Add the `spec-ste-check` skill with the CLI usage and the report reading.
- [ ] 4.5 Run `openspec validate enforce-ste-in-specs --type change --strict` before archive.
