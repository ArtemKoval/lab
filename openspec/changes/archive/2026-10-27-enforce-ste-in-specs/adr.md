# ADR Review Manifest

- Status: completed
- Review date: 2026-10-27

## Review Summary

ADR review completed for this change. The review examined the in-force records for conflicts with the enforcement decision. It found no conflict. The change operates inside the artifact discipline of ADR 0001. It keeps every surface on the single harness of ADR 0002. It extends the stdlib owned-mechanics pattern of ADR 0003 with one more small gate.

## In-Force ADRs Reviewed

- adr/0001-add-intent-driven-harness.md - this change carries the full artifact set and follows the two-merge discipline. The gate binds the specs that discipline produces. No supersession needed.
- adr/0002-claude-code-single-harness.md - the STE hook targets Claude Code only and lives under `.claude/`. No OpenCode mirror ships. No supersession needed.
- adr/0003-adopt-superpowers-execution-mechanics.md - the hook and the CLI follow the same vendored, owned, stdlib pattern as the charter hook and `plan_exec`. The CI suite this change extends is the job that record started. No supersession needed.

## New Durable ADRs Created

- adr/0004-enforce-ste-in-specs.md - the mechanical ASD-STE100 rule set as repo policy for spec text. One CLI is the rule authority. Enforcement runs at write time and at test time.
