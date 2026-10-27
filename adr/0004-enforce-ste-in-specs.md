# 0004 - Enforce ASD-STE100 in specs

- Status: accepted
- Date: 2026-10-27

## Context

CLAUDE.md makes ASD-STE100 the prose style for the repo, but only skill text carried the rule, so spec text drifted. Long sentences, seven uses of `provide`, and verb uses of `check` sat in the source-of-truth specs. A style that lives in prompts degrades on compaction and on other writers. The harness had one hook precedent and a root suite in CI, so a mechanical gate had two cheap places to run.

## Decision

All spec text under `openspec/specs/` and the active directories under `openspec/changes/` follows the mechanical ASD-STE100 rule set: word caps of 20 and 25, no semicolons, no contractions, no progressive tenses, and the banned words CLAUDE.md names, with a perfect tense as a warning. One stdlib CLI owns the rules. A pytest gate fails the root suite, and a `PreToolUse` hook blocks a non-STE write at edit time and fails open when the checker cannot run. Rejected options: skill text alone, because a wish is not a gate. A full approved-word dictionary, because it adds heavy data for the least gain. Coverage of `adr/`, `glossary/`, and the archive, because the user scoped the rule to specs.

## Consequences

Every spec write and every spec change passes one rule authority. The corpus got a one-time rewrite, and new violations surface at write time or test time. Regex heuristics carry false hits, so allowlists hold the attested exceptions and the corpus bounds the review. A future full-dictionary gate supersedes this record.
