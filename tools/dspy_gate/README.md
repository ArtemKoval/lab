# dspy_gate

The spec-governed gate system for this repository. The tool compiles
OpenSpec change scenarios into eval artifacts, and six gates prove that the
code matches the scenarios from proposal to production. The design comes from
the "Spec-Governed Agentic Systems" guide (issue 77).

## What it does

- **The bridge** parses a change's scenarios, compiles THEN clauses into
  assertion objects (tiers A, B, C), and writes the eval manifest
  (`openspec/eval_manifest.json`), one dataset per scenario
  (`openspec/changes/<id>/evals/`), and the generated Tier-A conformance
  module (`tests/dspy_gate/generated/`). The bridge is the only writer of
  these GENERATED paths; regeneration is deterministic and idempotent.
- **The gates**: Gate 0 lints a change (testable-or-reject, surface tags,
  rubric existence, policy bounds). Gate 1 proves bidirectional manifest
  coverage. Gate 2 optimizes and certifies on held-out scenarios. Gate 3 runs
  the delta and frozen suites. Gate 4 freezes suites and thresholds at
  archive. Gate 5 re-certifies when a model pin changes.
- **The harness registry** (`dspy_gate/harness/registry.py`) is the opt-in
  contract. Only the capabilities it declares are governed; the rest stay with
  the ordinary test suite.
- **The learning loop** (`nightly.py`) runs collect, triage, expand, optimize,
  certify, promote, and escalate over one run's failure rows, with the example
  bank (`bank.py`) as its memory and the five safety rails bound in.

## Commands

```bash
export PYTHONPATH=tools/dspy_gate
tools/zai_routing_audit/.venv/bin/python -m dspy_gate lint <change-id>
tools/zai_routing_audit/.venv/bin/python -m dspy_gate regen <change-id>
tools/zai_routing_audit/.venv/bin/python -m dspy_gate verify <change-id>
tools/zai_routing_audit/.venv/bin/python -m dspy_gate check-manifest <change-id>
tools/zai_routing_audit/.venv/bin/python -m dspy_gate status <change-id>
tools/zai_routing_audit/.venv/bin/python -m dspy_gate evals <change-id>
tools/zai_routing_audit/.venv/bin/python -m dspy_gate matrix <change-id>
tools/zai_routing_audit/.venv/bin/python -m dspy_gate freeze <change-id>
tools/zai_routing_audit/.venv/bin/python -m dspy_gate nightly <change-id> --from-report <rows.json>
```

Add `--json` for machine output. Exit 0 on success, 2 on any violation. The
`dspy-gate` skill and the feature-pipeline skill give the delivery-flow
placement.

## Setup

A clean clone needs nothing for the stdlib core beyond Python 3.11. The
registry unit `dspy-gate` runs the doctor:

```bash
python3 tools/dspy_gate_setup/dspy_gate_setup.py --repo-root .            # read-only
python3 tools/dspy_gate_setup/dspy_gate_setup.py --repo-root . --install  # shims + tool venv
```

The tool venv (`tools/dspy_gate/.venv`) carries the live paths: the MCP
wrapper (`mcp`), the optimizer and judges (`requirements-live.txt`, dspy 3.x),
and the browser journeys (`requirements-e2e.txt`, Playwright). The browser
journeys need `DSPY_GATE_E2E=1` and the chromium install; the live model paths
need `ZAI_API_KEY`.

## Model pins

`gates.yaml` pins glm-5.3-flash on every role, vision judge included, with
thinking disabled. This deviates from the guide's glm-5.3 and glm-4.5v pins on
purpose; ADR 0011 records the decision. Any pin change routes through Gate 5 re-certification.

## Gates on this tool

The root suite covers the tool at the 100 percent line and branch floor.
Mutation runs through the shared `tools/mutator` gate on an out-of-tree copy,
per the mutmut config in `pyproject.toml`.

## Known gaps (TBD)

- The GEPA optimizer path is wired behind the registry's `impl: optimized`
  routing but no governed module uses it yet; promotion is a one-line registry
  change plus a regeneration when one needs it.
- The e2e journeys bind to the fixture preview page only; a product surface
  binds to the same machinery with no rewrite when one exists.
- Tier-B certification for the pilot waits for an opt-in live run; the merge
  path burns no GLM spend.
