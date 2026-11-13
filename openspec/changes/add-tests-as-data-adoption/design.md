# Design: add-tests-as-data-adoption

## The analysis

The article Tests as data (Martin Fowler, 2026-11-11) describes
techniques for test suites that AI agents write. AI agents write many
tests. The tests can be hard to read. The tests can couple to the
implementation. Humans then lose trust in them. The element map below
compares each technique with this repository and gives the verdict.

| Article element | This repository today | Verdict |
| --- | --- | --- |
| Customer tests in the customer language | No customer-language tests exist. Inline `pytest.mark.parametrize` tables sit in 9 root test files, and the crm suite holds 36 more. The agent writes and owns them all. | Partial. Adopt through scenario tables in data files (candidate 1). The operator reads a table in proposal review, so the table gives the human the nearest seat to a customer test. |
| Black-box tests at system or component boundaries | The owned tools are stdlib CLIs. The CLI boundary is the natural seam. | Adopt inside candidate 1. Table rows drive the tool as a subprocess. |
| Tests-as-data: input, expected output, side effects, and setup as data | Only inline parametrize tables. No CSV or YAML case files exist. | Adopt. Candidate 1 moves the case data into files. Scalar values go in tables. Setup and side-effect rows defer to a later stage. |
| Structured GIVEN/WHEN/THEN scenarios for stateful cases | Not present. | Adopt inside candidate 1 as a later stage. The first delivery uses CSV only. YAML waits behind the test dependency policy. |
| Ad-hoc test DSLs with AI-generated runners | The dspy-gate bridge compiles governed scenarios into eval cases and generated Tier-A tests. | Partial. The governed lane exists. Candidate 1 gives the same idea a lighter form for the rest of the repo. |
| External DSL with parser-enforced assertions (Constrained Tests) | The dspy-gate scenario rule enforces assertions on governed scenarios. Parametrized runners make assertions mandatory elsewhere. | Skip. A custom parser per small CLI needs a reviewing customer. Most tools have no daily human reader. |
| Approval testing, approved logs, approved scenarios | Not present. `crm/port/port.py` diffs upstream file lists. No behavior lane exists. | Adopt for the crm port. Candidate 2 stores upstream outputs as approved data and reviews the diffs. Upstream behavior is the oracle. |
| Printers and parsers that project UI or state into text | The owned tools print text already. | Covered. The plain text output is the projection. No browser surface exists. |
| Mutation testing to validate the tests | The vendored mutator gate with the no-survivor bar plus the saturation ratchet (ADR 0014). | Covered. No new work. |
| Digital twins and local simulators for external services | floci runs the local AWS emulator in crm. The apfel local server judges the evals. ADR 0008 records the emulator decision with the proposed status. | Covered. The practice exists on the evidence of both setups. |
| Protecting the test harness (task type vs expected changed files) | `tests/claude_infra/test_gate_integrity.py` protects gate paths behind an acknowledgment line. The spec-gates-protect hook denies GENERATED writes. | Partial. Candidate 3 extends the pattern to tests-as-data files. |
| Not everything end-to-end. Service-layer and focused component tests | The tools are CLI-shaped, so the CLI boundary is the seam. No service layer exists. | Covered by the tool shape. |
| Executable specifications | The dspy-gate bridge covers registered capabilities only. Prose deltas stay the source of truth elsewhere. | Partial. No new work beyond candidate 1. The tables become executable. |
| Property-based testing as a complement | No property tests exist. The mutation bar proves assertion strength on known mutants. | Skip for now. The deferral sits in the open unknowns list. |

Two article limits need no row. The article names large steps as a
risk to human understanding. The pipeline already ships small reviewed
steps. The article exempts prototypes. The `fast:` prefix runs the
prototype flow in the pipeline.

## The adoption candidates

1. **The scenario tables.** A tests-as-data runner plus the first
   scenario tables for the owned tools. The operator is the reader, in
   proposal review and in gate review. The first delivery covers the
   runner plus tables for the pilot tool `spec_ste_check`. The pilot
   stays fixed. A second tool lands only when the pilot review asks
   for one. Case data sits in CSV files under the tool test area. A
   CLI
   row carries the input, the expected stdout and stderr, and the exit
   code. The runner drives the tool as a subprocess. A pure-function
   row carries input and expected pairs and runs in-process. Rows for
   setup state and side effects defer to a later stage. The first
   delivery adds new tables only. The inline tables convert later,
   when a change touches the tests of their tool. More tables land
   only after the operator reads a table during a review, and the
   review thread records the reading. Future change:
   `add-scenario-tables`.
2. **The port characterization lane.** An approval-test lane for crm
   ports. The lane stores approved logs of deterministic stdout
   surfaces from an upstream milestone. Scripted inputs drive the
   ported app and the upstream app the same way. The runner compares
   the outputs to the approved logs. The review records each
   deliberate deviation against the openspec change artifacts of the
   port. The determinism probe names the first milestone from the
   open milestone list of the port before it stores the first
   approved log. Future change: `add-port-characterization`.
3. **The test-data guard.** The protected-path pattern extended to
   tests-as-data files. The guard extends
   `tests/claude_infra/test_gate_integrity.py`. A pull request that
   edits a scenario table carries an acknowledgment line in its body.
   The guard reads the body from the event snapshot at create time.
   The operator merge of the pull request is the acknowledgment act.
   The open part is the file set that needs the line, and the rule
   that separates a silent edit from a reviewed edit. This candidate
   follows `add-scenario-tables`. Future change:
   `add-test-data-guard`.

The plan orders the candidates. The scenario tables land first. The
guard follows them, because it protects the files that the tables
create. The port lane has no dependency.

## The rejections

- Cucumber or Gherkin. The spec-as-source skill stays opt-in and not
  enabled. The STE scenario format and the dspy-gate bridge bind specs
  to tests already.
- A custom external DSL per tool. The dspy-gate scenario rule
  enforces assertions at the governed level. Parametrized runners make
  assertions mandatory for the rest. A parser per small CLI is
  overhead with no daily human reader.
- Property-based testing by default. This is a deferral, not a
  rejection. No policy governs a test-side dependency today, and the
  mutation bar does not find missing invariants. See the open unknowns
  list.
- Customer tests for a browser UI. No owned browser surface exists.
- A test-data framework per tool. One runner serves the owned tools.
  A framework per tool adds cost with no return.

## Edge cases and risks

- The customer seat is thin. The article needs a human customer who
  reads the tables. The operator is the only candidate reader. The
  first delivery stays small, and the expansion trigger guards the
  format against cost with no return.
- Table files can drift from the code under test. Candidate 1 puts
  each table next to its runner in the tool test area.
- An approved log can encode an upstream bug. Candidate 2 names the
  oracle in the review step. The oracle is upstream behavior at the
  pinned milestone. The review records each deliberate deviation.
- The guard can stop a legitimate table update. The acknowledgment
  line follows the gate-integrity precedent. The operator merge is the
  acknowledgment. The read model stays an open unknown until candidate
  3 states it.
- Many CLI rows make a suite slow. Candidate 1 keeps the first tables
  small. Pure-function rows run in-process. Subprocess rows stay few.

## Open unknowns

- The test dependency policy. Status: open. Next probe: candidate 1
  records which dependencies a test may add, and who approves them,
  before the runner lands.
- The property-based testing return trigger. Status: open. Next probe:
  name one concrete invariant that the mutation bar cannot hold, and
  open a probe change for it.
- The crm oracle determinism. Status: open. Next probe: candidate 2
  runs the determinism probe on one upstream milestone before it
  stores the first approved log.
- The guard read model. Status: open. Next probe: candidate 3 states
  the file set that needs the line, and the rule that separates a
  silent edit from a reviewed edit, before the guard lands.

## Verification

The artifacts carry the plan. No code ships here. The strict validate
passes on the change directory. The STE gate holds in two forms. The
`tools/spec_ste_check` CLI scans the Markdown spec text of the change
directory before the push, because the Write hook cannot see worktree
paths. The pytest gate `tests/spec_ste_check/test_ste_gate.py` scans
the same scope in the root suite. The scan reads Markdown files only,
so the CSV and YAML data files of the future changes stay outside the
gate. This design draws no C4 diagram. The comparison table carries
the structure, and the candidates are future changes. The three
adoption candidates become issues or changes of their own when the
operator orders them.
