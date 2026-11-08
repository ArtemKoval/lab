---
name: saturation-run
description: Run the saturation pass over the owned tools and hold the per-module ratchet. Use when the user asks to run a saturation pass, to refresh the saturation store, to init the saturation baseline, or to find which owned module lost mutation score. Gives the commands, the exit codes, and the store rules.
---

# saturation-run

## What it does

`tools/saturation_pass/saturation_pass.py` runs the vendored mutator
over each owned Python tool with that tool's area suite, parses the
printed per-function table, aggregates it into per-module scores, and
refuses any per-module score drop against the committed store at
`reports/saturation/scores.json`. The store moves only through pull
requests. The scheduled workflow (`.github/workflows/saturation.yml`)
runs the same CLI in enforcement mode and never writes the store.

## Before you run it

The pass reads the gate coverage report. Produce it first when it is
missing:

```bash
tools/zai_routing_audit/.venv/bin/python -m coverage run \
  --data-file=target/coverage/python/.coverage \
  --source=tools/plan_exec,tools/spec_ste_check,tools/devcontainer_init,tools/handover_telemetry,tools/handover_telemetry_setup,tools/dspy_gate,tools/dspy_gate_setup,tools/peak_hours_gate,tools/process_issues,tools/saturation_pass,tests \
  -m pytest -q tests
tools/zai_routing_audit/.venv/bin/python -m coverage lcov \
  --data-file=target/coverage/python/.coverage \
  -o target/coverage/python/lcov.info
```

The mutator runs one area suite per mutant, so a full pass takes
minutes to about an hour depending on the site count.

## Commands

```bash
# Run the pass in enforcement mode (compares against the store)
python3 tools/saturation_pass/saturation_pass.py --tool spec_ste_check

# Run every owned tool
python3 tools/saturation_pass/saturation_pass.py

# Write the first baseline (refuses an existing store)
python3 tools/saturation_pass/saturation_pass.py --init

# Merge a clean run into the store (land it through a pull request)
python3 tools/saturation_pass/saturation_pass.py --update
```

## Reading results

Exit 0 holds or improves every module score. Exit 2 refuses the run
and names the reason on stderr: a drop with both scores, a scoreless
module, a failed tool, a missing store with the `--init` hint, or a
missing coverage report with the `--coverage` hint. `--json PATH`
writes the run report with every module verdict.

## Rules

- A score drop means a mutant survived where the tests used to kill
  it. Fix it with tests, never by editing the store.
- Land `--update` results through a pull request, one tool per
  change when the run is large.
- The scheduled workflow enforces; no CI step writes the store.
