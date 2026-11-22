# ADR Review Manifest

- Status: completed
- Review date: 2026-11-20

## Review Summary

ADR review completed for this change. One new durable ADR records the
lesson-ledger decision, and no in-force ADR conflicts with it.

## In-Force ADRs Reviewed

Reviewed all in-force ADRs from `adr/0001` to `adr/0020` for conflicts with
the attempt-ledger decision. The nearest areas:

- ADR 0004 (the mechanical spec rule set) — governs spec text style. No
  conflict. The delta spec follows it.
- ADR 0007 (the pack vocabulary clause) — governs engine vocabulary, not
  the harness loop. No conflict.
- ADR 0016 (the fast-mode delivery contract) — governs pipeline delivery
  modes. The change adds no delivery mode. No conflict.
- ADR 0020 (pack policy carries the routing rules) — governs crm packs. No
  conflict.

No in-force ADR records a lesson-record format, a consultation rule, or a
write-back rule. The decision opens new ground.

## New Durable ADRs Created

- `adr/0021-harness-lessons-carry-attempt-ledgers.md` — the harness lessons
  carry attempt ledgers: a problem line, attempts with predicted-versus-
  observed outcomes and a setting, and a verdict. The implementation PR
  lands it in the house custom format. The Decision prose records the
  rejected options: mechanical enforcement through a repo guard or a
  plan-file convention, and diagnosis-only records without the outcome
  ledger.
