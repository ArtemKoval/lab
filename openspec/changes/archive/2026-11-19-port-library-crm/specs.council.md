# Council Notes: specs/

## Author Summary

The five delta specs port byte-faithful requirement blocks from the child's
live specs, assembled by the primary agent. The reviewer challenged format
and fidelity. The gherkin-authoring skill review ran before this round and
found the structure sound: 36 requirements, 62 scenarios, bold
GIVEN/WHEN/THEN steps, no duplicate requirement names.

## Reviewer Challenges

- The three new-capability deltas lost the child Purpose sections, which
  the archive flow copies into the live specs, with a fallback warning
  otherwise. (CONFIRMED)
- Two deltas carried a double blank line after the ADDED header.
  (CONFIRMED)
- The crm-engine delta covers exactly the 7 child-only requirements, and
  the crm-domain-pack delta covers exactly the vocabulary requirement.
  (CONFIRMED correct)

## Resolutions

- Accepted: the three deltas carry the child Purpose sections verbatim
  before `## ADDED Requirements`, in the house delta shape.
- Accepted: the blank lines are normalized to one.
- No change: the two modified-capability deltas were already exact.
- Accepted late: the dspy-gate lint in CI rejected the change, because the
  scenario id `the-lead-declines-the-request` appeared twice. The two
  scenarios were byte-identical under two requirements, a defect the
  child's own gates never caught. The second scenario is renamed to
  `the-posted-decline-becomes-the-decision`. This rename is the one
  deliberate text deviation from byte fidelity, and the bridge regen
  refreshed the eval manifest entry for the change.

## Remaining Risks

- The ported scenarios carry no surface tags. The capabilities stay outside
  the governed registry, and a promoting change can retag them later.
- The archive sync must find the delta text identical to the child live
  specs, byte for byte, which the assembly by extraction preserves.
