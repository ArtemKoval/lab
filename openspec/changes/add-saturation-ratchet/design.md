# Design: add-saturation-ratchet

## Plan review

The inner-loop review consulted the saturation report, the gate tools,
the nightly workflow shape, and the process_issues runner seam. The
grill pass ran at pipeline Step 0: the operator approved the four
proposal scope, the both-placements answer (CLI plus scheduled
workflow), and the exit-0 CI bar. The review settled these decisions:

- One CLI, one engine. The CLI reuses the vendored mutator as the only
  mutation engine and adds no engine of its own. The CLI parses the
  printed per-function table of the mutator and aggregates it into
  per-module scores by the namespace column. CI already parses the
  `Total` row of the same table with awk. The `.edn` snapshots would
  need an EDN parser that the standard library does not carry.
- The per-tool table holds nine Python-bearing tools from the CI gate
  list. `project_setup` holds only `registry.json` and carries no
  product Python, so the table names nine tools: `plan_exec`,
  `spec_ste_check`, `devcontainer_init`, `handover_telemetry`,
  `handover_telemetry_setup`, `dspy_gate`, `dspy_gate_setup`,
  `peak_hours_gate`, and `process_issues`. Each entry carries the
  product path and the test suite path of that tool. The
  `handover_telemetry_setup` entry points at `tests/handover_telemetry`,
  because no dedicated directory exists. The shared zai venv
  interpreter runs every suite.
- The test command of each tool is that tool's own suite under
  `tests/<tool>`, not the root suite. The per-pull-request gate runs
  the root suite because a diff carries few mutants and the runtime
  stays bounded. A whole-tree pass at the root-suite cost is hours:
  187 sites at about 30 seconds per mutant run for one tool. The
  measured saturation rate of about 48 mutants per minute holds only
  with sub-second area suites, and that is the rate the whole-tree
  projection needs. The ratchet starts from the area-suite baseline,
  and the per-pull-request gate stays the stronger per-diff guard.
- The coverage report comes from one root-suite run before the pass.
  The CLI reads it with `--use-existing-coverage` and
  `--coverage PATH` with the house default path. The workflow builds
  the same three venvs as the test workflow.
- The store lives at `reports/saturation/scores.json`. The house rules
  put metrics under version control at a stable path, and `reports/`
  is the metric home. The store carries one entry per tool with one
  score per module under the mutator namespace keys, the site count,
  and a run stamp. The store schema carries `schema` 1.
- The ratchet compares module by module. A run score below the stored
  score fails the run. A module absent from the store is record-only,
  because the per-pull-request gate already holds new code to zero
  survivors at birth. A missing store fails with the `--init` hint, so
  a baseline never appears by accident. An `n/a` module score never
  holds or improves, so a coverage-less pass cannot slip through as a
  silent clean run.
- The workflow enforces and never writes the store. A CI push to main
  would skip the review guards, so the store moves only through pull
  requests: the operator or the loop runs `--update` locally after a
  clean run and lands it through the normal review. The workflow
  uploads the JSON run report as an artifact for the record.
- The workflow carries a `timeout-minutes` budget of 90 and a
  concurrency group, and it runs only when the expression
  `vars.SATURATION_PASS_ENABLED != 'false'` holds. The default-on
  schedule answers the operator decision for a scheduled pass. The
  polarity differs from the nightly's opt-in `== 'true'`: the nightly
  burns model spend, so it refuses without configuration, and this
  pass burns only runner minutes, so it runs unless the operator sets
  the variable to `false`. A fresh fork runs the pass out of the box.
  The contract test pins the exact expression.
- The runner seam mirrors `process_issues`. The CLI takes one
  dispatchable runner over the mutator argv and one dispatchable clock
  beside it, so the tests stay hermetic with no mutation run, no
  coverage dependency, and no real-time stamp dependence.
- The registry unit is `saturation-pass` with the stdlib shape of the
  `sec-scan` unit: a check command and a no-op install line. The
  implementation wires `tools/saturation_pass` into the four CI gate
  lists of the test workflow, so the new tool sits under the same
  gates as the other owned tools. The diff touches
  `.github/workflows/tests.yml`, a protected path, so the
  implementation pull request carries the `gate-integrity:
  acknowledged` line and the merge is the acknowledgment.
- The two setup tools (`handover_telemetry_setup`, `dspy_gate_setup`)
  carry real functions and real sites, so the degenerate no-table case
  is unlikely. The baseline records their site counts in the pull
  request description, so a zero-site entry surfaces once, at the
  baseline.
- Amendment, found by the first baseline attempt: dspy_gate holds
  namespaces with zero mutable sites (the `mcp_server` wrapper, the
  `harness.registry` and `harness.triage` modules, and the
  `harness.preview` handler class), and the first n/a rule conflated
  them with coverage gaps. The rule now separates the two: a
  namespace with zero aggregated sites carries no mutants and stays
  out of the report and the store, while a namespace with sites but
  no executed mutants fails the run. The delta scenario pins the
  split.

## Diagram

Container level, ASCII, lightweight C4-inspired. Assumption: one
runner per execution, no queue. Open question: none at this level.

```
  operator / loop agent                       GitHub Actions (cron, dispatch)
       |                                              |
       v                                              v
  +----------------------------------------------------------+
  |                saturation_pass CLI                        |
  |  (tools/saturation_pass, stdlib)                          |
  |  reads the tool table, runs one mutator pass per tool,    |
  |  parses the per-module table, compares, reports, updates  |
  +-------+------------------++------------------+-----------+
          |                  ||                  |
   invokes (argv)     reads (lcov)     reads / writes
          v                  v                  v
  +----------------+  +----------------+  +------------------------------+
  | mutator        |  | gate coverage  |  | reports/saturation/          |
  | (vendored)     |  | report (lcov)  |  | scores.json (committed)      |
  +-------+--------+  +----------------+  +------------------------------+
          | runs
          v
  +------------------------------+
  | per-tool test suite          |
  | (tests/<tool>, shared venv)  |
  +------------------------------+
```

Bullets:

- Boundary one: the CLI is the only new runtime unit. It wraps the
  existing mutator and adds no engine.
- The mutator stays the mutation authority. The CLI never computes a
  score itself. The CLI parses the printed table.
- The store is the only new durable state, and the workflow never
  writes it.
- The scheduled workflow is an alternate caller of the same CLI, not a
  second implementation.
- Assumption: the gate venvs and the shared venv exist on the caller.
  The registry installs them. CI builds them.

## ASIT pass

- Unification: the mutator is the engine. The nightly workflow donates
  the cron shape and the variable-gate and artifact patterns. The
  pinned cron value is weekly and differs from the nightly daily
  value, and the concurrency block is new. The process_issues CLI
  donates the runner seam and the exit contract. sec_scan donates the
  registry unit shape. The house store pattern puts the metric under
  `reports/`.
- Multiplication: the per-tool table entry is a slightly modified copy
  of one record shape, nine times.
- Division: parsing, comparison, store input and output, and the
  runner stay separate functions, each at complexity 10 or less.
- Breaking symmetry: `--init` (baseline, no comparison) sits apart
  from the default run (ratchet on) and `--update` (write after a
  clean run).
- Object removal: no new mutation engine, no evaluation service, no
  database, no store-writing CI step. The vendored mutator plus a
  parser and a comparator cover the need.

The rejected alternatives: extend the vendored mutator (upstream layout
and pin stay clean), parse the `.edn` snapshots (no stdlib EDN parser),
store writes from CI (no pushes to main outside review), a whole-tree
pass on pull requests (ADR 0005 rejected it for unbounded runtime).

## Adversarial authoring round

The adversarial-authoring skill ran one round on the proposal and the
spec delta. The challenger settled these points, and the artifacts
carry the fixes:

- The ratchet must name both scores in the refusal, so a drop report
  is actionable without a second run. The scenario carries both.
- A missing store must fail with the `--init` hint instead of silently
  becoming the baseline. The scenario carries the hint.
- `--update` must refuse a violating run, not only the plain run. The
  scenario carries the refusal.
- The workflow contract test must assert the absence of store write
  steps, not only the presence of the steps it needs. The scenario
  carries the absence assertion.
- The proposal now says the per-pull-request resolution change lands
  in a separate change, so the two changes never blur.
