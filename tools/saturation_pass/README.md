# saturation_pass

A stdlib CLI that runs the vendored mutator over the owned tools and
holds the per-module saturation ratchet. Proposal 2 of
`reports/2026-11-08-issue-123-saturation-testing-analysis.md`; the
OpenSpec change `add-saturation-ratchet` owns the behavior.

## Why

The per-pull-request mutation gate sees only the diff. A module
outside a pull request can rot while every pull request stays green.
The saturation pass measures the whole surface per owned tool, keeps
the per-module scores in a committed store, and refuses a drop.

## The tool table

Nine owned tools, from the CI gate list minus `project_setup` (which
carries no product Python): `plan_exec`, `spec_ste_check`,
`devcontainer_init`, `handover_telemetry`, `handover_telemetry_setup`,
`dspy_gate`, `dspy_gate_setup`, `peak_hours_gate`, `process_issues`.
Each entry carries the product path and the area suite path. The
`handover_telemetry_setup` suite lives under `tests/handover_telemetry`.

## Run

The pass reads the gate coverage report first (the mutator discovers
`target/coverage/python/lcov.info` itself):

```bash
tools/zai_routing_audit/.venv/bin/python -m coverage run \
  --data-file=target/coverage/python/.coverage \
  --source=tools/plan_exec,tools/spec_ste_check,tools/devcontainer_init,tools/handover_telemetry,tools/handover_telemetry_setup,tools/dspy_gate,tools/dspy_gate_setup,tools/peak_hours_gate,tools/process_issues,tools/saturation_pass,tests \
  -m pytest -q tests
tools/zai_routing_audit/.venv/bin/python -m coverage lcov \
  --data-file=target/coverage/python/.coverage \
  -o target/coverage/python/lcov.info

python3 tools/saturation_pass/saturation_pass.py --tool spec_ste_check
python3 tools/saturation_pass/saturation_pass.py            # all nine
python3 tools/saturation_pass/saturation_pass.py --init     # first baseline
python3 tools/saturation_pass/saturation_pass.py --update   # store write
```

Exit 0 holds or improves every module score. Exit 2 refuses the run
and names the reason on stderr. `--json PATH` writes the run report.

## The store

`reports/saturation/scores.json`, schema 1: one entry per tool with a
`stamp` and one module entry per mutator namespace (`sites` integer,
`score` float with one decimal). The store moves only through pull
requests: `--update` locally after a clean run, then a normal review.
The scheduled workflow runs the CLI in enforcement mode with `--json`
and never writes the store.

## The workflow

`.github/workflows/saturation.yml`: weekly cron `37 4 * * 1`, plus
`workflow_dispatch` with a comma-separated `tools` input.
`timeout-minutes: 90`, concurrency group `saturation-<ref>`, and the
escape variable: the job runs unless
`vars.SATURATION_PASS_ENABLED` is exactly `false`. The pass fails the
workflow on any ratchet refusal, so a drop appears on the schedule.

## Tests

`tests/saturation_pass/` holds the unit tests over the parser, the
comparator, the store, and the actions, with the runner and clock
seams. `tests/claude_infra/test_saturation_workflow.py` pins the
workflow shape.
