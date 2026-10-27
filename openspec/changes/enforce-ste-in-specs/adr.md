# ADR Review Manifest

- Status: completed
- Review date: 2026-10-27

## Review Summary

ADR review completed for this change. The review examined the in-force records for conflicts with the enforcement decision and found none: this change operates inside the artifact discipline ADR 0001 established, keeps every surface on the single harness ADR 0002 fixed, and extends the stdlib owned-mechanics pattern ADR 0003 set with one more small gate.

## In-Force ADRs Reviewed

- adr/0001-add-intent-driven-harness.md - this change carries the full artifact set and follows the two-merge discipline; the gate binds the specs that discipline produces. No supersession needed.
- adr/0002-claude-code-single-harness.md - the STE hook targets Claude Code only and lives under `.claude/`; no OpenCode mirror ships. No supersession needed.
- adr/0003-adopt-superpowers-execution-mechanics.md - the hook and the CLI follow the same vendored, owned, stdlib pattern as the charter hook and `plan_exec`; the CI suite this change extends is the job that record started. No supersession needed.

## New Durable ADRs Created

- adr/0004-enforce-ste-in-specs.md - the mechanical ASD-STE100 rule set as repo policy for spec text, one CLI as the rule authority, and enforcement at write time and test time.
