# ADR review: add-library-domain

## Records examined

- ADR 0007 owns the seam: the engine carries generic nouns, and a pack keeps
  its domain words. The library pack follows it. No new engine noun appears,
  so no superseding record is due.
- ADR 0010 owns the history discipline of the assignment pull requests. The
  delivery of this change merges with merge commits and atomic commits.
- ADR 0008 owns the emulator first rule for the AWS targets. This change
  touches no AWS wiring. The devcontainer and floci runs of the assignment
  follow the skill, not a new record.

## New records

None. The pack is an instance of the pack contract, and ADR 0007 is the
durable record for that shape. The loan term mapping and the arithmetic
boundary stay in `design.md`, because they bind one pack, not the engine.

## Consequences

A future copy table or borrower login in the engine needs a superseding
record for new engine nouns. The follow-ups in HARNESS.md name that path.
