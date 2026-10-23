# 0001 - Adopt the intent-driven harness

- Status: accepted
- Date: 2026-10-23

## Context

The lab runs every change through one delivery pipeline. The pipeline records requirements, but decisions, clarifying questions, and review pressure between changes had no durable home. The intent-driven template provides those pieces around OpenSpec as a schema, skills, and agents.

## Decision

Adopt the intent-driven schema and its ported surfaces in this harness. Proposal artifacts merge to main before apply starts. Implementation merges before archive runs. Durable decisions live in immutable records under adr/ and change only through supersession.

## Consequences

Every future change carries proposal, Gherkin specs, design, an ADR manifest, and tasks. Three small squash-merge PRs replace one merge per change. The spec-as-source layer ships installed but disabled. A CLI update that changes the experimental schema format needs a one-change migration.
