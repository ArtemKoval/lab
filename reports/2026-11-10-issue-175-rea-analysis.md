# Analysis: rea — what this lab can port

- Issue: ArtemKoval/lab#175
- Source: https://github.com/morluto/rea, MIT license. Main branch at
  commit e9b6c87 (2026-11-09), npm package rea-agents 6.8.0.
- Date: 2026-11-10
- Status: analysis only. The proposals in section 6 need approval. Each
  proposal becomes a separate change with its own review through the
  feature pipeline.

## 1. Scope

This run examines rea and maps its mechanisms to the harness surfaces in
this repository. This run does not change any skill, hook, or tool. rea
is a reverse engineering toolkit, and this lab studies agent harnesses,
not binaries. A port of the product has no workload here. The port plan
in section 6 covers mechanisms only: the tool registry, the evidence
model, the error algebra, the setup flow, and the governance artifacts.
The run worked from a read-only clone and four read-only examinations of
the source. Section 3 names the mechanisms this lab already covers.
Section 5 lists the candidates this run defers, with reasons. Section 6
lists the proposals in value-versus-effort order. The user selects the
proposals to build. Each build is a separate change with its own review
and gates.

## 2. What rea is

rea ("Reverse Engineer Anything") is a local-only reverse engineering
toolkit with one MCP server and one CLI. An agent calls rea through MCP
to inspect a target, and rea returns findings with their evidence. The
same workflows run from a terminal. The scale is more than one million
lines of TypeScript across 52 top-level source directories. The MIT
repository carries about 446,000 stars. Static inspection of many
formats needs no analysis engine. Deep native analysis uses an
installation of Hopper, Ghidra, IDA, or Kuna that the caller supplies,
through Python, Java, and Swift bridges.

The dependencies flow inward. The domain layer holds pure types, zod
schemas, a 10-line Result type, and the Evidence record. The contracts
layer declares every tool once. The application layer owns the
services. The composition layer wires providers into services. The
server and CLI layers register the same capabilities as MCP tools and
terminal commands.

The disciplines that matter for this lab:

1. **A contract-first tool registry.** One contract record declares
   each tool: name, kind, input schema, output schema, effects,
   annotations, and examples. About 160 tools share one handler
   pipeline: validate, log, execute, record, deliver. The catalog is
   generated data, the runtime hashes its identity digest, and the
   build records the digest.
2. **Evidence with confidence, authority, and unknowns.** Each evidence
   record carries a content-digest id, raw and normalized results, a
   confidence of observed, derived, or inferred, an authority enum, and
   a limitations list. An unknown is a first-class record with a
   revision chain and separate links to supporting and contradicting
   evidence.
3. **A tagged error algebra with remediation.** A 10-line Result type
   and 27 error tags carry a user message, a remediation action that
   the producer owns, secret-safe diagnostics, and the evidence that
   the run produced before the failure.
4. **Honest schema advertisement.** The compact profile bounds an
   advertised input schema under a 13 KB budget, with a reduced form as
   the fallback. Validation never weakens. Only the advertisement
   shrinks.
5. **Setup as a consented, verified write.** A declarative registry of
   28 clients drives detection. Detection does not imply consent.
   Setup plans in the open, asks twice, makes backups, writes, reads
   the result again, and restores the prior state on a mismatch.
6. **Ownership and lifecycle discipline.** rea names one owner for
   each interpretation and resource. Unresolved identity stays unknown. A
   process run token, not a PID, proves ownership. Cleanup reports
   cleaned: false with a reason instead of assumed success.
7. **Governance artifacts with generated proof.** rea keeps a
   generated error contract schema and a 125-row audit of user-visible
   error copy. Testing lanes follow the rule that a skipped lane
   implies no coverage. Lifecycle regression tables pair scenarios
   with assertions. SHA-256 owner digests bind the obligation ledgers.

## 3. What this lab already covers

The two systems agree on several designs. These mechanisms need no port:

| rea | This lab |
| --- | --- |
| ADR convention with Nygard sections, prose only | Numbered ADRs in adr/ with the superseding rule, and the change flow that owns them |
| Stryker scans that gate on report completion, not on score | The vendored mutator gates on no survivors, a stricter bar |
| Generated-file freshness verification in the task graph | The dspy-gate bridge owns GENERATED paths, and the protect hook denies a hand edit |
| A spec directory with contract fixtures | OpenSpec specs as the source of truth, and the six dspy-gate gates |
| A CI guard against failure-hiding pipes | The lesson in memory: a gate verdict must gate with its own exit code |
| PR readiness attestation, and never claim an unrun test | The verification-before-completion skill |
| Review thread rules: root cause, structural fix, validation | The charter review-and-merge discipline |
| A setup registry of 28 agents | tools/project_setup/registry.json, and the project-setup skill |
| knip rules against dead exports | The CRAP gate flags complex uncovered code. A trivial dead export passes today, so P6 scans for it |
| Redaction rules for diagnostics | The cc-logging hook and the handover telemetry tool redact at write time |

## 4. Mechanisms this run examined in detail

**A contract registry with one handler pipeline.** A contract record is the single source of truth for one tool
(src/contracts/toolContractTypes.ts). The record holds the name, the
title, the kind, a requiresActiveTarget flag, the zod input and output
schemas, the effects, the annotations, and the examples. Forty-seven
group arrays across the per-domain contract files form one ordered
list, TOOL_CONTRACTS (src/contracts/toolContracts.ts). The MCP side registers each contract
through one shared pipeline that validates, logs, executes, records,
and delivers (src/server/contractToolHandler.ts). The CLI side imports
the same application service and the same zod shapes, and reshapes only
the arguments and the delivery (src/cli/sqliteCommands.ts). A family id
list stays free of schemas, so a CLI start never loads the contract
graph (src/contracts/toolFamilyIds.ts). The tool catalog is generated
data (docs/reference/mcp-contracts.md), and catalogIdentity.ts hashes
the identity of every tool for stability verification. The repository
guidelines bind handlers to named contracts, and a name-keyed admission
path runs each operation by tool name (src/server/admittedToolOperation.ts).

**Honest schema advertisement.** The compact profile bounds each advertised input schema under a 13 KB
budget (src/config/mcpInputSchemaProfile.ts). The ladder inlines
references first, then reduces to names, types, and required flags, and
finally gives a description-only form
(src/contracts/compactInputSchema.ts). Server validation keeps the full
canonical schemas in every profile. A source comment names the client
limit in the profile module (src/config/mcpInputSchemaProfile.ts). One
model API rejects any tool schema past that measured cap. The
contracts guide adds the depth limit from strict clients and the
gateway rules against oneOf forms (docs/reference/mcp-contracts.md).
The hot-cold catalog advertises four tools plus a discover_tools search
page, and enables tools in place after the client refreshes its tool
list (src/server/ProgressiveToolCatalog.ts).

**Evidence, bundles, and residual unknowns.** The Evidence record is the unit of proof (src/domain/evidence.ts). Its
id is a content digest over semantic content, and display metadata such
as the caller path stays outside the id. Re-parsing authenticates the
digest, so tampering produces a mismatch error. Each record carries raw
and normalized results, a confidence of observed, derived, or inferred,
and an authority enum. It also carries the execution environment, typed
locations, and a limitations list. Downstream tools accept an evidence
reference or an evidence file path, and refuse a digest mismatch. An
unknown is a record with its own digest id and a revision chain. Its
status is open, investigating, blocked, contradicted, or resolved. It
keeps separate links to supporting and contradicting evidence
(src/domain/residualUnknown.ts). Updates use optimistic concurrency
through an expected revision.

**A tagged error algebra.** The Result type is 10 lines with no dependencies (src/domain/result.ts).
Expected failures extend one error base, and each subclass carries a
literal tag from a closed list of 27 tags
(src/domain/analysisErrorBase.ts). The base holds the user message, the
remediation action, secret-safe diagnostics, captured output, a cleanup
chain, and a method that attaches partial evidence to the failure. A
producer owns its remediation sentence. For example, a concurrency cap
error carries the counts and the advice to wait for an active command
to finish. Retryability is a separate field, and the two never appear
together in one recovery variant.

**Provider adapters and limitations.** Each provider exports an identity constant and a pure argv builder with
no process input or output (src/objdump/ObjdumpCommand.ts). The rizin
adapter adds a limitations function that states what the adapter cannot
attest about its own command (src/rizin/RizinCommand.ts). The shared
service owns every process execution. The composition layer binds each
executable through a REA_<X>_COMMAND environment override
(src/composition/reverseEngineering.ts). Availability and target
support return closed unions with explicit unknown states, so an
adapter cannot guess.

**Process ownership.** A run token proves process ownership, not a PID with a path
(src/process/ProcessOwnership.ts). The reader takes the token only from
the environment of the process itself, and distinguishes absent from
unavailable (src/process/ProcessRunTokenObservations.ts). Cleanup
re-reads the process table and revalidates the group against the
recorded command and parent. It plans the signal, and reports
cleaned: false with a reason when a group reappears. A lease type gives
cross-process, single-owner semantics with typed failure kinds
(src/process/OwnedLease.ts).

**The setup flow.** A declarative table describes 28 supported clients with their config
paths, marker paths, skill directories, and config formats
(src/application/SupportedClients.ts). Setup runs a read-only doctor
first. It offers every detected client unselected, and preselects only
registrations that rea owns. Two confirm stages separate the selection
from the approval. The approval shows exact paths, backup paths,
commands, environment keys, and network origins. A --yes flag without a
scope flag covers only rea-owned registrations. The writer keeps the
first backup file. It preserves a digest-named recovery copy when the
bytes differ. It publishes through a staged path, reads the written
file again, and restores the prior state on a mismatch
(src/application/SetupClientConfiguration.ts). Setup refuses to replace
any registration whose owner identity it cannot prove
(src/application/ClientRegistrationIdentity.ts). The entry script
refuses a project-scoped write for a client that does not support one
(scripts/rea.mjs).

**Governance artifacts with generated proof.** The error contract is a generated JSON Schema with code, category,
retryable, remediation, and typed recovery variants
(docs/error-contract.schema.json). A CSV audit lists 125 user-visible
error strings with harm rank, trigger, risk, replacement copy,
implementation status, and verification result
(docs/user-visible-errors.csv). The task graph verifies the freshness
of every generated artifact against the committed output (turbo.json).
The testing discipline defines seven behavior depths with admission
limits (docs/development/testing.md). It names the lifecycle
regressions that an ownership or cleanup change must cover as scenario
and assertion pairs. The lanes document names more than 30
real-toolchain lanes with exact preconditions, and states the rule that
a skipped lane implies no coverage (docs/testing-lanes.md). The
deterministic suite runs on every pull request, and the real-toolchain
lanes run in separate, path-filtered workflows. An obligation ledger
tool binds each reconstruction claim to an owner manifest and to
positive, negative, and malformed fixtures
(docs/reference/reconstruction-obligation-ledgers.md). Each claim also
binds to a validator, and the bundle shows the validator result. A
SHA-256 owner digest binds each obligation.

## 5. Candidates this run defers, with reasons

- **The analysis engines.** The binary, Electron, Android, web, and
  firmware engines answer analyst questions about software artifacts.
  This lab produces no such questions, so a port of the product has no
  workload here.
- **The contract registry at rea scale.** rea registers about 160
  tools across two surfaces, and the registry earns its cost there.
  This lab exposes two small MCP servers, and the rubric in P5 covers
  the need.
- **Compact and hot-cold schema profiles.** No lab client rejects a lab
  schema today. The trigger for a port is a schema that a client
  refuses, or a server with more than about ten tools. The mechanism to
  port then is the ladder in section 4.
- **RL environments.** The AgentEnv builder builds runnable
  environments from recorded API sessions for training runs. This lab
  runs no RL training.
- **Run-token process ownership.** No lab tool supervises foreign
  processes. The residue scan reads git state, and the charter already
  binds worktree removal to the worktrees this pipeline created.
- **Obligation ledger machinery.** The ledger binds reconstruction
  claims to fixtures and validators. The lab equivalent, a claim of
  done, already binds to commands and their output through the
  verification-before-completion skill.
- **The error copy audit CSV.** The audit ranks harm across a large
  error surface for a mass-market tool. This lab serves one operator.
- **release-please and 27-client detection.** The lab ships no releases
  and drives one agent harness.
- **knip production reachability proofs.** The lab builds no production
  bundle. P6 gives the dead-export scan.

## 6. Proposals

Order: value against effort.

### P1. A remediation rule for tool failures — high value, low effort

Every rea error carries a remediation action that the producer owns,
and retryability is a separate field. The CLI contract in Step 2 of
the feature pipeline fixes exit codes, but says nothing about the
failure text. A user who sees exit 2 does not always see the next
action.

- Change: Step 2 of the feature pipeline gains one rule. Every
  operational failure names one next action in its message, and a
  --json failure carries a remediation field beside the code. New and
  touched tools adopt the rule.
- ASIT: Unification. The exit-code contract in Step 2 exists, and the
  rule extends its message shape.

### P2. Confidence and unknown discipline for reports and handover issues — high value, low effort

rea grades every finding as observed, derived, or inferred, with an
authority class and a limitations list, and records an unknown as a
first-class item with a status. Lab reports and handover issues state
findings in prose, and an uncertain claim looks the same as a verified
one.

- Change: the report and handover conventions gain three rules. Each
  finding carries a confidence of observed, derived, or inferred. Each
  limitation enters a limitations list, not the finding text. Each open
  unknown enters a list with a status and a next probe. The handover
  issue template gains the two lists.
- ASIT: Unification. The reports directory and the handover template
  exist, and the rules extend their shapes.

### P3. Consent and backup-verify mechanics for project-setup — medium value, medium effort

rea plans every write in the open, asks for approval twice, keeps
backups, and reads the written file again before it claims success. The
project-setup skill examines the registry and asks for permission. It
states no plan shape, no backup rule, and no verification of a write.
No setup doctor covers the project-setup registry. This proposal
outranks the low-effort proposals below it, because a wrong setup
write is destructive.

- Change: the project-setup skill gains the mechanics as written rules,
  and a new setup doctor in the house doctor contract gains them as
  code. The plan names every target path and every unit before any
  write. Detection selects nothing, and only registry-owned units
  preselect. The installer makes a backup copy of each file it
  replaces, reads each written file again, and reports a mismatch as a
  failure. Any blanket consent flag covers only registry-owned state.
- ASIT: Multiplication, with the justification that the consent rules
  need one code owner. The doctor contract in Step 8 of the feature
  pipeline is the existing pattern, and the new doctor is one instance
  of it.

### P4. Testing-lane honesty and lifecycle regression tables — medium value, low effort

rea states the rule that a skipped lane implies no coverage, and pairs
every lifecycle scenario with the assertions that prove it. The lab
gates e2e work behind environment variables, and a skipped e2e mark is
easy to read as coverage.

- Change: Step 3 and Step 9 of the feature pipeline gain the rules. A
  skipped lane implies no coverage, and the pull request body names
  each skipped lane. A change to code with cleanup, cancellation, or
  ownership behavior lists its lifecycle scenarios. The list covers
  success, cleanup failure, cancellation mid-run, and partial
  completion, and names the test that holds each scenario.
- ASIT: Unification. The e2e marks and the gates exist, and the rules
  extend their reading.

### P5. A tool admission rubric — medium value, low effort

rea adds a tool only when an analyst question needs it, shapes tools
into six forms, and prefers primitives over composed workflows. The lab
adds a tool per task, and CLAUDE.md says nothing about the shape of the
next tool.

- Change: Step 2 of the feature pipeline gains the rubric. A new tool
  names the question it answers. It picks one of six shapes: inspect,
  search-list, trace, compare, workflow, observe-capture. It prefers a
  primitive over a composed workflow, and gives one owner to each
  interpretation it produces.
- ASIT: Unification. The step exists, and the rubric extends its plan
  rules.

### P6. An opt-in dead-export scan — medium value, low effort

rea runs knip with all ten rules at error level, and a dead export
fails the build. The lab gates cover complexity, coverage, duplication,
and mutation. A trivial dead export passes every lab gate today,
because no test imports it and the mutator cannot see it.

- Change: a scan tool in the house style runs the Python dead code
  detector vulture over the owned tools behind an opt-in flag, in the
  pattern of sec-scan. The scan starts as an opt-in report. A later
  change promotes it to a gate when the first run names real residue.
- ASIT: Multiplication, with the justification that no existing gate
  sees a trivial dead export. The sec-scan tool is the existing
  pattern for a scanner in the house style, and the new scan is a
  second instance of that pattern.

