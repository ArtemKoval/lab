# Design: add-saturation-ci-bar

## Plan review

The grill pass ran at pipeline Step 0: the operator picked exit 0 over
keeping the 95 percent resolution. The review consulted the workflow,
the contract pin, and the current surfaces: the loop engine holds exit
0 on its full pass, and the checker joined it after the survivor fix,
so no current surface regresses. The review settled these decisions:

- Object Removal: the resolution block leaves the workflow. The
  mutator's own exit codes already carry the contract. The awk
  resolution re-interpreted exit 3 against a floor that the house
  contract never needed. The step becomes a bare invocation: exit 0
  passes, any non-zero exit fails the pull request.
- The contract pin updates in the same change, because the workflow
  and its pin protect each other. The pin asserts that the resolution
  string and the mutation log path are gone, the direct invocation
  stays, and the comment names the saturation bar.
- The spec gains the bar as a formal requirement, because the 95
  percent resolution was never a requirement. It lived in the
  workflow and the Purpose sentence only. The Purpose sentence moves
  to the bar in the implementation PR, beside the delta, because the
  archive sync cannot rewrite Purpose text.
- The feature-pipeline skill's gate line moves from the score floor
  to the saturation bar, so the delivery rules and CI agree on one
  bar.

## ASIT pass

- Object Removal: the awk resolution block, the tee, and the score
  awk leave the workflow. The mutator's own exit codes carry the
  contract.
- Unification: the contract test already pins workflow properties.
  It grows one assertion for the bar.
- No new component. The gate stays diff-scoped with the root suite,
  per ADR 0005 and the scheduled pass boundary of ADR 0014.

## Adversarial authoring round

The adversarial-authoring pair ran one round. The challenger
verified the pins, the spec text, and the workflow block, and settled
these points, and the artifacts carry the fixes:

- The resolution removal is the only workflow edit. No other step
  changes. The scenario carries a clean-run pass case, so the
  requirement is two-sided.
- The Purpose sentence edit lands in the impl PR (not the archive),
  because the archive sync cannot rewrite Purpose text.
- The skill line update lands in the impl PR.
- Current surfaces stay green, so the bar does not regress any
  current surface.

## Bounds

No governed capability, so no gate thresholds. This change's own code
meets the local mutation rule with no survivors. The CI resolution
for changed paths rises to the saturation bar in the implementation.
