# Design: add-dspy-gate

## Source

Issue #77, "DSPy Gate", with the attached guide "Spec-Governed Agentic Systems".
The scope decision at Step 0 builds the full guide, phases 0 through 4, in one change.
The model decision pins glm-5.3-flash on every text role and keeps glm-5.3-flash on the vision judge.

## Plan review

The grill round settled three forks: the fixture preview page for the e2e surface, the default-off nightly
run, and the gate-status MCP server. The adversarial pair on the proposal folded five major findings into
the artifacts: the `mcp` package pin, the settings-key amendments, the gate run sites, the STE collision
with GENERATED markdown, and the banned word forms. The root suite stays hermetic: the live paths sit
behind lazy imports and env gates, and the tests stub the dspy module.

## Diagrams

Format: ASCII in fenced blocks. Rigor: lightweight C4-inspired. Both choices are assumptions. The repo
holds no diagram precedent, and ASCII renders in the terminal.

### Container diagram

```text
                       +---------------------+     +--------------------+
     human reviewer -->| openspec/           |<----| Claude Code        |
                       | intent + thresholds |     | session (Loop 2)   |
                       +---------+-----------+     +---------+----------+
                                 ^  |                       |  ^
                       regen     |  | propose, edit         |  | gates via CLI
                                 |  v                       |  v
                       +---------+---------------------------+----------+
                       | dspy_gate CLI                                   |
                       | lint, regen, manifest, evals, optimize, bank,   |
                       | nightly, matrix, freeze, status                 |
                       +---+---------------+----------------+------------+
                           |               |                |
              writes       |    serves     |   queries      |
        +------------------+    +-----------+     +----------+
        v                      v                          v
+--------------------+  +---------------------+  +---------------------+
| GENERATED artifacts|  | fixture preview     |  | dspy-gate MCP server|
| manifest, evals,   |  | page (http.server)  |  | status + matrix     |
| generated tests,   |  +---------+-----------+  +---------------------+
| baselines, bank,   |            |
| artifacts/         |            | drives
+--------------------+            v
        ^               +---------------------+        +----------------+
        | certify       | Playwright browser  |        | z.ai GLM API   |
        | (env-gated)   | (DSPY_GATE_E2E=1)   |        | (key-gated)    |
        +---------------+---------------------+        +-------+--------+
                                                               |
                                                 +-------------v---------+
                                                 | GitHub Actions        |
                                                 | tests, spec-gates,    |
                                                 | nightly (default off) |
                                                 +-----------------------+
```

### Gate flow along the change lifecycle

```text
propose --> [Gate 0 lint] --> proposal PR --> merge --> apply branch
                                                          |
                     spec edit --> bridge regen --> [Gate 1 coverage]
                                                          |
              [Gate 2 optimize+certify] (only impl: optimized, key-gated)
                                                          |
                     implementation PR --> [Gate 3 delta + frozen suites]
                                                          |
                     merge --> archive --> [Gate 4 freeze] --> archive PR
                                                          |
                     model pin change --> [Gate 5 re-certify frozen suites]
                                                          |
                     nightly (default off) --> learning loop --> drafts + PRs
```

### Bridge component sketch

```text
dspy_gate/
  scenarioparse.py  headings, tags, WHEN/THEN, stable slugs
  lint.py           Gate 0 rules, policy bounds
  compile.py        THEN to Tier A, B, C assertion objects
  manifest.py       eval_manifest.json writer and verifier (Gate 1)
  datasets.py       per-scenario JSONL emitters
  codegen.py        generated Tier-A pytest with GENERATED headers
  gatepolicy.py     gates.yaml reader, bounds, pins
  checks.py         Tier A, C, D runners (stdlib)
  judge.py          Tier B ensemble, visual judge (lazy dspy)
  lm.py             the one model factory (lazy dspy)
  optimize.py       Gate 2 runner (lazy dspy)
  evals.py          Gate 3 delta and frozen suite runner
  freeze.py         Gate 4 archive freeze
  bank.py           example bank store, judge gate, eviction
  nightly.py        seven-step loop orchestration
  matrix.py         conformance matrix for the PR
  harness/          triage hand module, preview server, registry of modules
  mcp_server.py     thin wrapper, no logic of its own
```

## Key decisions

- House layout: `tools/dspy_gate/dspy_gate/` with `cli.py` and `__main__.py`, plus `pyproject.toml`,
  `ruff.toml`, `requirements.txt`, `requirements-dev.txt`, and `README.md`. A doctor lands at
  `tools/dspy_gate_setup/` and a unit joins the registry.
- The root suite stays hermetic. `lm.py`, `judge.py`, and `optimize.py` import dspy inside their
  functions. The tests stub the dspy module through `sys.modules`, so no test touches the network.
  Live runs need `ZAI_API_KEY`, and browser runs need `DSPY_GATE_E2E=1`.
- Generated artifacts stay JSON, JSONL, or Python. This keeps the STE scan off generated files, since
  the STE CLI reads markdown only. The protect hook denies edits to every GENERATED path.
- Gate triggers: Gate 0 on the proposal flow and on spec edits through the bridge hook. Gate 1 in CI on
  every pull request and locally before a push. Gate 2 on demand through the CLI for a module with
  impl optimized. Gate 3 in the root suite for Tier A and in CI for delta and frozen suites. Gate 4 in
  the archive flow. Gate 5 in CI on a model pin diff without a fresh green frozen-suite record.
- `gates.yaml` split: the effective policy lives at `tools/dspy_gate/gates.yaml`. Each change carries
  its thresholds in `openspec/changes/<id>/gates.yaml`. Gate 4 freezes the capability thresholds beside
  the frozen suites at `openspec/specs/<capability>/`, so an archive sync cannot lose them.
- Coverage: the root suite adds `tools/dspy_gate` to its 100 percent floor in the same change. The
  generated conformance tests count toward the floor, and the tasks sequence tests with code.
- The MCP wrapper follows the zai-routing-audit pattern: the `mcp` package with the pin `>=1.2.0,<2`,
  tools that call CLI runners, and stub tests at the root suite. The registration lands in `.mcp.json`
  and in the two settings keys, and the intent-driven-harness delta amends those requirements.
- The nightly workflow carries cron and dispatch triggers. The job condition tests
  `vars.DSPY_NIGHTLY_ENABLED == 'true'`. The first step refuses to run the loop when
  `ZAI_API_KEY` is absent, so a missing secret burns nothing. The spec scenarios hold under both paths.
- The pilot capability rides the same change: its scenarios compile through the bridge, and its
  generated Tier-A tests prove the pipeline end to end on the implementation PR.

## The registry opt-in rule

One registry rule settles a recursion the review missed: the harness registry is
the opt-in contract. Gate 0 eval rules, the manifest, and the datasets govern
only the capabilities the registry declares. Capabilities outside the registry,
such as the machinery specs of this very change, stay with the ordinary suite.
Without the rule, the change that ships the gate system could not pass its own
Gate 0.

## Builder check

One fresh builder read the artifacts and asked twelve questions. Three got answers in the
artifacts, seven settled as defaults, and two governance calls settled on guide grounds:

- Manifest shape: `{"version": 1, "changes": {"<change-id>": [cases]}}`. Each case holds
  `scenario_id`, `capability`, `surface`, `gates`, `tier`, `assertion`, `dataset_path`,
  `generated_test`, `impl`, `entry_point` or `artifact_dir`, and `source_hash`. A dataset record
  holds `scenario_id`, `inputs`, and `expected`.
- GENERATED header forms: JSON carries a `_generated` first key, JSONL a first `#` line, Python a
  module docstring. No header carries a timestamp, so regeneration stays byte-identical.
- The Gate 5 certification ledger is `openspec/specs/<capability>/certs.jsonl` with the pins digest,
  the tier results, the date, and the source. Gate 2 writes a row on a green certification, and
  Gate 3 writes a row on a green frozen-suite run. Drift compares the current pins digest with the
  last row. The protect hook denies hand edits to the ledger.
- The nightly draft area is `openspec/drafts/<slug>/`, outside `openspec/changes/`, so Gate 0,
  Gate 1, and the bridge never process drafts.
- Tier D reads usage and latency from a live run record. For a hand module or a hermetic run it
  reports n-a and stays green. It goes red only on a live run over the ceiling.
- Generated tests import the harness through the `tests/dspy_gate/conftest.py` path insert, on the
  house pattern. The manifest path anchors at the repo root. A judged-only scenario emits no
  Tier-A test, so the root suite stays green with no network.
- An AND under a judged THEN folds into that scenario Tier-B reference. An AND under a Tier-A THEN
  becomes an extra Tier-A assertion. A rubric path resolves against the change root.
- Visual baselines are hand-authored in the change PR, so the protect hook exempts
  `openspec/specs/**/visual/` and keeps the optimizer artifacts and the other GENERATED globs denied.
- The change sets `tier_b_min` at 0.80. The rubric scores 1.0, 0.5, or 0.0, so an ensemble mean of
  0.80 needs two full passes with one partial. The bounds allow 0.60 to 1.00.
- The pilot certifies Tier A only on the implementation pull request. Tier B certifies later
  through an opt-in live run, so the pipeline burns no GLM spend on a merge.

## Deviations from the guide

- glm-5.3-flash replaces every glm-5.3 pin, and thinking stays disabled everywhere. The guide warns
  that thinking plus low temperature loops, so the flash roles run at the flash profile. An ADR
  records this at archive as `adr/0010-adopt-spec-governed-agent-gates.md`.
- The lab layout nests the guide's root-level `scripts/`, `harness/`, and `datasets/` inside the tool
  package and the openspec tree. The guide's names survive as module names.
- Playwright comes as the Python package, on the crm precedent of a governed install step.
- The MCP server ships in this change. The guide marks it optional, and the user asked for it.

## Failure modes

- The parser and the openspec CLI drift apart: Gate 0 runs `openspec validate --strict` first, and the
  parser stays the final enforcement point with exit 2 and the scenario named.
- dspy API drift: the requirement pins dspy 3.x in the live extra, the stub keeps the root suite
  independent, and the live path stays env-gated.
- GLM truncation or loops: thinking stays disabled, and each role carries its token ceiling in
  `gates.yaml`.
- A missing `ZAI_API_KEY`: every live path exits 2 and names the variable.
- A hand edit to a GENERATED file: the protect hook denies it, and `bridge --check` fails on drift in
  CI. The fix is a regeneration, never an edit.
- A scenario rename: Gate 1 flags the orphan or missing case. A rename is a spec migration that
  regenerates the change, per the guide warning that IDs are forever.
