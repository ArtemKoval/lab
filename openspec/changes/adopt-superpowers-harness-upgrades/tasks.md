## 1. SessionStart charter hook

- [x] 1.1 Write `.claude/hooks/harness-charter.sh` (mode 100755, `#!/bin/bash`, builtin-only, exact `hookSpecificOutput` envelope, fallback context, always exit 0) per design D2
- [x] 1.2 Write `.claude/hooks/charter.md` (40-60 lines, STE, pointers plus gate names, the four drift-pin strings) per design D3
- [x] 1.3 Wire the `hooks.SessionStart` group into `.claude/settings.json` through the update-config skill (direct command, `timeout: 10`, `async: false`), confirmed against the hooks reference
- [x] 1.4 Write `tests/claude_infra/test_harness_charter.py`: envelope, escape, fallback, settings shape, key preservation, exec bit, target exists, line bound, drift-pin strings
- [ ] 1.5 Live-fire the hook (fresh session, `/clear`, confirm the charter lands) and record the runtime in the handover notes

## 2. plan_exec tooling

- [x] 2.1 Create `tools/plan_exec/plan_exec/{__init__,__main__,cli,brief,package,ledger}.py`, `pyproject.toml` (mutmut config), `ruff.toml` (mirror zai, py312, C901 max 10), and `tests/plan_exec/conftest.py` with the two-candidate sys.path insert and `MUTANT_UNDER_TEST` stand-down
- [x] 2.2 Implement `brief` with tests covering both plan shapes, dotted ids, and the three exit-2 cases (100% branch coverage)
- [x] 2.3 Implement `package` with tests using local git repos with `-c user.email`/`-c user.name` fixtures and the exit-2 cases
- [x] 2.4 Implement `ledger` with tests for identity, abs-path compare, append formats, and the exit-2 cases
- [x] 2.5 Write `tools/plan_exec/README.md` (commands, exit codes, shared-venv note, mutation recipe with the rsync excludes `.venv`, `__pycache__`, `.ruff_cache`, single-writer note)
- [x] 2.6 Add `.plan_exec/` to `.gitignore` and `tools/plan_exec/plan_exec/__main__.py` to the `.coveragerc` omit list
- [x] 2.7 Run the gates: coverage 100% branch, ruff clean, mutmut on an out-of-tree copy at 95% or higher with the unmutated copy green first
- [x] 2.8 Add the plan_exec section to the `openspec-apply-change` skill

## 3. Adoption skills

- [x] 3.1 Port `systematic-debugging` (four phases, three-fix architecture question, house gates referenced) per design D7
- [x] 3.2 Port `verification-before-completion` (claim-command-output table, verify-change boundary)
- [x] 3.3 Port `writing-skills` (baseline-first loop, form-to-failure table, Agent-tool pressure scenarios)
- [x] 3.4 Add the provenance contract test for the three skills; leave `PORTED_SKILLS` and the six-rule count untouched

## 4. Pipeline and CLAUDE.md edits

- [x] 4.1 Edit `feature-pipeline/SKILL.md`: review-reception block (Step 11/12), model-selection rule (inner loop and Step 12), discard contract and worktree provenance cleanup (Step 13), builder check (Step 1.5); keep the four drift-pin strings (`OpenSpec`, `openspec-git-discipline`, `Nothing proceeds on red`, `adversarial-reviewer`) intact in the file
- [x] 4.2 Remove the two stale "no hooks yet" statements from the same file
- [x] 4.3 Add the plan_exec entry to the CLAUDE.md projects list and the charter hook to the harness surfaces line
- [x] 4.4 Extend the pipeline contract test with the five rule marker strings and the no-stale-claim check

## 5. ADR and records

- [x] 5.1 Verify `adr/0003-adopt-superpowers-execution-mechanics.md` on main (house format, accepted, no Supersedes) — it already landed with the proposal PR
- [x] 5.2 Record `custom` in `.claude/skills/architectural-decision-records/preferences.md` with the house-format note

## 6. CI

- [x] 6.1 Write `.github/workflows/tests.yml` (pull_request + push to main + workflow_dispatch, paths-ignore fde/llm_ops, ubuntu-24.04, setup-python 3.12, repo venv, pytest with the plan_exec coverage floor, ruff on plan_exec)
- [x] 6.2 Add the workflow contract test (interpreter, coverage step, ruff step present)

## 7. Verification and close-out

- [x] 7.1 Run the full hermetic suite and the claude_infra contract tests through the repo venv interpreter; both green
- [x] 7.2 Run the plan_exec gates (coverage floor, ruff, mutation) and record the scores
- [x] 7.3 Dogfood: run this change's `tasks.md` through `brief`, track the implementation in the `ledger`, package the implementation diff with `package` for review
- [ ] 7.4 Run the adversarial diff review round on the implementation branch; fix confirmed findings
- [ ] 7.5 Open the handover issue after the merge (template sections, PR link, merged commit, hook runtime, gate scores, secrets removed)
