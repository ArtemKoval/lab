# Tasks: add-process-issues

## 1. The scan tool

- [x] 1.1 Create `tools/process_issues/process_issues/core.py` with the pure `classify` function, the label precedence rule, and the state constants.
- [x] 1.2 Create `tools/process_issues/process_issues/cli.py` with the `scan` subcommand, the `--json` flag, the injectable `gh` runner, and the exit contract 0 and 2.
- [x] 1.3 Create `tools/process_issues/process_issues/__init__.py` and `tools/process_issues/process_issues/__main__.py` as the house shims.
- [x] 1.4 Create `tools/process_issues/ruff.toml` with the C901 complexity gate and `tools/process_issues/pyproject.toml` with the mutmut config.

## 2. The scan tests

- [x] 2.1 Create `tests/process_issues/conftest.py` with the house sys.path bootstrap and the `MUTANT_UNDER_TEST` guard.
- [x] 2.2 Create `tests/process_issues/test_process_issues_core.py` for the precedence rule, the contradiction cases, and the oldest-first order.
- [x] 2.3 Create `tests/process_issues/test_process_issues_cli.py` for the `scan` output, the `--json` payload, and the exit contract with a stubbed `gh` runner.

## 3. The skill

- [x] 3.1 Create `.claude/skills/process-issues/SKILL.md` with the loop procedure, the phase rules, the fold rule, the failure rules, and the single-run discipline.
- [x] 3.2 Keep the skill under 90 lines. Name the scan command and the label repair command in it. Name the pre-flight command from the `peak-hours-gate` skill.

## 4. The GitHub and settings wiring

- [ ] 4.1 Create the labels `waiting-human-approval`, `human-approved`, and `answered` on the GitHub repo through `gh label create`.
- [x] 4.2 Add the `gh` allow rules from the proposal Impact list to `.claude/settings.json` through the `update-config` skill.
- [x] 4.3 Add the `gh-cli` unit to `tools/project_setup/registry.json` with the `gh --version` test and the platform install note.

## 5. The CI and coverage wiring

- [x] 5.1 Add `--cov process_issues` to `.github/workflows/tests.yml` and the tool to the crapper and dryer sources.
- [x] 5.2 Add the pinned substrings to `tests/claude_infra/test_ci_workflow.py`.
- [x] 5.3 Add the `tools/process_issues/process_issues/__main__.py` omit line to `.coveragerc`.

## 6. The docs

- [x] 6.1 Create `tools/process_issues/README.md` with the purpose, the scan command, and the exit codes.
- [x] 6.2 Add the `tools/process_issues` line to the Projects section of `CLAUDE.md`.

## 7. The gates and the review

- [x] 7.1 Run `python -m pytest` and make the full hermetic suite green.
- [x] 7.2 Run the three quality gates on the new paths with the shared zai venv interpreter.
- [x] 7.3 Run `openspec validate add-process-issues --type change --strict` with no errors.
- [x] 7.4 Run `python -m dspy_gate lint add-process-issues` and `python -m dspy_gate verify add-process-issues` with no violations.
- [x] 7.5 Run the adversarial whole-diff review on the implementation diff, and fix every confirmed finding.
- [ ] 7.6 Create `adr/0012-grant-the-loop-the-automation-authority.md` from the manifest during the archive step, and make sure the file lands in `adr/`.
