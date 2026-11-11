# Proposal: add-bench-adoption-plan

## Why

Issue 208 asks for an analysis of the agentic harness at
`github.com/ed-donner/bench` and a plan for what this repository
should adopt. Bench is a four-app teaching monorepo whose harness —
short role-split working documents, a one-command pre-handover bar, a
controls-layers table, and a Stop-hook backstop — encodes practices
this repository runs differently or not at all. The analysis and the
adoption decisions belong in a reviewed artifact, not in a chat
reply.

## What Changes

### The analysis

Design.md carries the element-by-element comparison: every harness
element bench runs, mapped against what this repository already has,
with an adopt, partial, or skip verdict and the reason.

### Three adoption candidates for future changes

- A single local entry that runs the pipeline's fast gates over the
  changed paths.
- A controls-layers table in CLAUDE.md that names, for every gate
  this repository runs, whether it gates or backs up.
- A Stop-hook backstop that runs the fast gates on turn end, blocks
  once per session, and hands the failures back.

Each becomes its own future change with its own review. This change
ships none of them.

### The rejections

Lefthook, advisory duplication, gitleaks, the SPEC-to-PLAN flow,
strict TypeScript linting, and browser verification stay out, each
with the reason in design.md.

## Capabilities

### New Capabilities

None. The change is an analysis and adoption plan. The adoptions are
future changes of their own.

### Modified Capabilities

None.

## Out of scope

- No code, workflow, or settings change ships here.
- No adoption change starts from this run.

## Impact

- `openspec/changes/add-bench-adoption-plan/`: the artifacts.
- No product code, no gate wiring, no registry unit.
