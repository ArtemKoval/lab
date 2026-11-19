# 0019 - Pack vocabulary and award units

- Status: accepted
- Date: 2026-11-12
- Ported from: ArtemKoval/library_crm adr/0011 (2026-11-12), renumbered
  because the lab ledger owns 0010 through 0017, with the status line
  normalized to the lab house syntax.

## Context

The packs speak their domains in their data, their rules, and their
protocol's `summarize` lines, but the dashboard hardcodes the insurance
words for field labels, and it reads the insurance fields of the contract
record directly. On the library pack the case page renders a travel policy.
The engine's award is a plain number, and a pack's award can carry a non
money unit: the library pack's award is a loan term in days, so every
`money()` call over an award prints "$14.00" for a 14-day term, and the
backend's approval-limit refusals interpolate `dollars(limit)` for a limit
that is days. ADR 0007 says new engine vocabulary beyond its nouns needs a
superseding record. The unit words `money` and `days` are such vocabulary.

## Decision

The pack's manifest MAY carry a `vocabulary` section: a `labels` map from
stable key ids to the pack's words, a `contract` presentation of a title
and labeled rows over the contract record's fields, an `award_format` of
`money` or `days`, and `messages`, the pack's words for the refusal family
that names the limit. The pack endpoint serves the section. The dashboard
renders labels through one lookup with today's English words as fallback,
renders the contract from the pack's rows, and formats awards and the
limit through the pack's unit. A pack with no vocabulary section renders
exactly as today, until it declares its words.

## Consequences

- The packs own their words. A pack's demo reads as its domain, and a new
  pack needs no dashboard edit to speak correctly.
- The engine carries two unit words, `money` and `days`, which this ADR
  records under ADR 0007's clause.
- The core keeps the current words as fallbacks and the current contract
  panel for packs without a vocabulary section. Retiring that legacy panel
  happens when every pack declares its words.
- Two formatters exist, in TypeScript and in Python, and parity tests hold
  them together.
