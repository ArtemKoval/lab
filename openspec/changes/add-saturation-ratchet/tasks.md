# Tasks: add-saturation-ratchet

## 1 Tool

- [ ] 1.1 Create `tools/saturation_pass/saturation_pass.py`: the
  per-tool table with nine entries, the mutator runner seam and the
  clock seam, the per-function table parser with the namespace
  aggregation, the module comparator, the store reader and writer, and
  the CLI with `--init`, `--update`, `--tool`, `--coverage`,
  `--store`, `--json PATH`, and the exit contract 0 or 2.
- [ ] 1.2 Add `tests/saturation_pass/` unit tests over every new
  function with a fake mutator table: the parser, the comparator, the
  store reader and writer, the action routing, and the refusal
  messages. The tests stay hermetic and never run a real mutation.
- [ ] 1.3 Add `tools/saturation_pass/README.md`: purpose, the tool
  table, the store, the actions, and the exact commands.

## 2 Workflow

- [ ] 2.1 Add `.github/workflows/saturation.yml`: weekly cron,
  `workflow_dispatch` with a tools input, `timeout-minutes: 90`, a
  concurrency group, the `SATURATION_PASS_ENABLED` variable gate, the
  three gate venvs and the shared venv, one root-suite coverage pass,
  the pass CLI, and the report artifact upload. No store write steps.
- [ ] 2.2 Add `tests/claude_infra/test_saturation_workflow.py`: the
  contract test that pins the cron value, the dispatch input, the
  variable expression, the timeout, the concurrency group,
  `cancel-in-progress` false, the artifact upload, and the absence of
  store write steps and push steps.
- [ ] 2.3 Extend `.github/workflows/tests.yml` and
  `tests/claude_infra/test_ci_workflow.py` so `tools/saturation_pass`
  joins the coverage list, the gate whitelist, and the ruff list of
  the test workflow.
- [ ] 2.4 Carry the regenerated `openspec/eval_manifest.json` into the
  implementation pull request. The bridge regenerates it. Never hand
  edit it.

## 3 Wiring

- [ ] 3.1 Add the `saturation-pass` unit to
  `tools/project_setup/registry.json` in the stdlib shape of the
  `sec-scan` unit, and satisfy the project-setup completeness test.
- [ ] 3.2 Add `.claude/skills/saturation-run/SKILL.md` and the CLAUDE.md
  project line.

## 4 Baseline and gates

- [ ] 4.1 Run the root-suite coverage pass with `--source` over the
  nine product paths and `tests`, convert it to the house lcov path,
  then run the pass CLI with `--init` and land
  `reports/saturation/scores.json` as the first baseline. Record the
  per-tool site counts in the pull request description.
- [ ] 4.2 Land `adr/0014-scheduled-saturation-pass.md`.
- [ ] 4.3 Run the full hermetic suite, the branch-coverage floor, the
  CRAP gate, and the mutation gate on the changed code, and run
  `openspec validate add-saturation-ratchet --type change --strict`.
- [ ] 4.4 Open the implementation pull request with the line
  `gate-integrity: acknowledged` in the body, because the diff adds
  `.github/workflows/saturation.yml` and edits
  `.github/workflows/tests.yml`. The merge is the acknowledgment.
