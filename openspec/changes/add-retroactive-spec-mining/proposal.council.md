# Council Notes: proposal.md

## Author Summary

The change adds one opt-in, read-only stdlib CLI at `tools/spec_mining/`
with three miners (working tree, archive drift, git history) and no LLM in
the tool. Output lands in `reports/spec_mining/<UTC-date>/` as
`coverage.json`, `report.md`, and seed drafts that stay outside
`openspec/changes/`. One new capability `spec-mining`, no modified
capabilities, no gates, no registry unit, no workflow wiring. The skill
converts a user-chosen seed through the normal propose flow with approval.

## Reviewer Challenges

- [blocker] The first What Changes bullet held one 31-word sentence. The
  STE gate fails it on the 25-word descriptive cap.
- [major] The census numbers in the Why (18 tools, 41 skills) did not match
  the repo counts and rot quickly.
- [major] The Impact line "No change to `openspec/specs/`,
  `openspec/changes/`" contradicted the change contract. The change adds
  `specs/spec-mining/` and lives under `openspec/changes/`.
- [major] The locked `--json` flag was absent from the CLI bullet.
- [major] Impact omitted the CI coverage source and the quality-gate wiring
  that house proposals carry.
- [minor] The no-MCP non-goal was nowhere in the draft.
- [minor] The interpreter path is a gitignored path that a clean clone
  lacks. House form states the fallback.
- [minor] `- (none)` with the dash is the house form under Modified
  Capabilities.
- [minor] "each archived change" overstates the scope. Some archives carry
  no delta.
- [minor] The capability description should name the three sources.
- Question: does `spec_mining` enter the saturation-pass owned-tools table,
  which the spec holds at exactly nine names?

## Resolutions

- Accepted: the long sentence is split into short sentences.
- Accepted: the census is now approximate wording.
- Accepted: the Impact specs line states the delta addition and says that
  no existing spec changes.
- Accepted: `--json` joins the CLI bullet.
- Accepted: a Wiring bullet names the CI coverage source and the three
  quality gates.
- Accepted: the no-MCP, no-registry-unit, and table-at-nine non-goals are
  one What Changes bullet.
- Accepted: the interpreter sentence uses the house fallback form.
- Accepted: Modified Capabilities uses `- (none)`.
- Accepted: the archive miner bullet says "each archived change with a
  delta".
- Accepted: the capability description names the tree, the archive, and the
  git history.
- Rejected: none. All findings got verification against the repo before
  the fix.
- Deferred: none.

## Remaining Risks

- The saturation table stays at nine by residue-scan precedent. A future
  change can add the tool to the ratchet if the operator wants it.
- The exact CI coverage config files are an implementation concern that
  design.md and tasks.md pin.
- The seed text sits outside the STE hook. The skill must run
  `tools/spec_ste_check` when a seed moves into `openspec/changes/`.
