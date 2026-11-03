---
name: dspy-gate
description: Run the spec-governed gate system — compile OpenSpec scenarios into eval artifacts, run the six gates, optimize and certify governed modules, and read gate status. Use this skill when the user asks to run a spec gate, regenerate eval artifacts, lint a change, examine gate status or the conformance matrix, freeze a change at archive, or re-certify after a model pin change.
---

# dspy-gate

The tool at `tools/dspy_gate/` compiles OpenSpec change scenarios into the eval
manifest, the datasets, and the generated Tier-A conformance tests, and runs
the six gates over them. The harness registry
(`dspy_gate/harness/registry.py`) is the opt-in contract: only the capabilities
it declares are governed. The feature-pipeline skill owns the gate placement in
the delivery flow.

## Commands

Run from the repository root. The shared repository venv interpreter carries
the stdlib core; the tool venv carries the live paths.

```bash
PYTHONPATH=tools/dspy_gate tools/zai_routing_audit/.venv/bin/python -m dspy_gate lint add-dspy-gate
PYTHONPATH=tools/dspy_gate tools/zai_routing_audit/.venv/bin/python -m dspy_gate regen add-dspy-gate
PYTHONPATH=tools/dspy_gate tools/zai_routing_audit/.venv/bin/python -m dspy_gate verify add-dspy-gate
PYTHONPATH=tools/dspy_gate tools/zai_routing_audit/.venv/bin/python -m dspy_gate check-manifest add-dspy-gate
PYTHONPATH=tools/dspy_gate tools/zai_routing_audit/.venv/bin/python -m dspy_gate status add-dspy-gate
```

Add `--json` for machine output. The exit contract is 0 on success and 2 on
operational failure. The subcommands:

- `lint <change-id>` — Gate 0: openspec validate, testable-or-reject, surface
  tags, rubric existence, policy bounds.
- `regen <change-id>` — regenerate the manifest, the datasets, and the
  generated tests from the spec. The bridge is the only writer.
- `verify <change-id>` — fast staleness check; the bridge hook runs it after
  every spec edit.
- `check-manifest <change-id>` — Gate 1: bidirectional scenario coverage.
- `evals <change-id>` — Gate 3: the delta and frozen suites with failure
  routes. Requires the generated artifacts.
- `matrix <change-id>` — the conformance matrix for the pull request body.
- `freeze <change-id>` — Gate 4: copy eval cases and thresholds beside the
  capability at archive.
- `optimize` paths — Gate 2: the holdout split, the certify-on-held-out run,
  and the artifact write. A live run needs `ZAI_API_KEY`.

## Gates and routing

Gate failures route to re-optimize, fix the harness, change the spec (a new
proposal), or repair the environment. The report names the route. Never edit a
GENERATED path: the protect hook denies it, and regeneration is the fix.

## Model pins

`tools/dspy_gate/gates.yaml` pins glm-5.3-flash on every text role and
glm-4.5v on the vision judge, with thinking disabled. Any pin change routes
through Gate 5 re-certification against the frozen suites.

## Exit codes

0 on success. 2 on any gate violation, stale generation, missing manifest, or
missing provider key.
