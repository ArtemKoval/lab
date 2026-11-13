# Proposal: add-tests-as-data-adoption

## Why

Issue 215 asks for an analysis of the article Tests as data (Martin
Fowler, 2026-11-11). The article names techniques that make large
agent-written test suites readable and trustworthy. This repository
owns many small CLI tools. The agent writes most of their tests. The
analysis and the adoption decisions belong in a reviewed artifact, not
in a chat reply.

## What Changes

### The analysis

Design.md carries the element-by-element comparison. Each technique
in the article maps against what this repository already runs, and
Design.md records two article limits without rows. Each row carries
an adopt, covered, partial, or skip verdict with the reason.

### Three adoption candidates for future changes

The plan orders the work. The scenario tables land first. The guard
follows them, because it protects the files that the tables create.
The port lane has no dependency.

- `add-scenario-tables`: a tests-as-data runner plus the first
  scenario tables for the owned tools. Case data lives in CSV files,
  and thin parametrized pytest runners read it. The first delivery
  covers the pilot tool `spec_ste_check`, and a second tool follows
  only when the pilot review asks for one.
- `add-port-characterization`: an approved-log characterization lane
  for crm ports. Scripted inputs drive the ported app. The runner
  compares the outputs to approved logs from the upstream milestone.
- `add-test-data-guard`: the protected-path pattern extended to
  tests-as-data files, with an acknowledgment line in the pull request
  body.

Each becomes its own future change with its own review. This change
ships none of them.

### The rejections and the deferral

Cucumber or Gherkin, a custom external DSL per tool, customer tests
for a browser UI, and a test-data framework per tool stay out. Each
rejection carries its reason in design.md. Property-based testing by
default is a deferral, not a rejection. Design.md carries the
deferral in the open unknowns list.

## Capabilities

### New Capabilities

None. The change is an analysis and adoption plan. The adoptions are
future changes of their own.

### Modified Capabilities

None.

## Out of scope

- No code, test, workflow, or settings change ships here.
- No adoption change starts from this run.

## Impact

- `openspec/changes/add-tests-as-data-adoption/`: the artifacts.
- No product code, no gate wiring, no registry unit, no spec delta.
