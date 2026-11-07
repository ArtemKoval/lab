# Council Notes: spec.md

## Author Summary

The delta adds four requirements to the process-issues capability: the
run lock protocol, the scan refusal on a fresh foreign lock, the stale
rules that keep the loop wedge-free, and the halt-first pre-flight. The
delta restates the scan CLI requirement with the lock examination order
and the exit-64 usage rule. Sixteen scenarios cover the contract edges.

## Reviewer Challenges

- The exit contract needs the full MODIFIED text at proposal time, with
  exit 64 named and exit 2 kept as one category.
- A refused scan needs the zero-gh-call anchor as an observable result.
- The corrupt record, the foreign host, the reboot, and the age rule all
  need their own scenarios, because each rule heals one wedge path.
- The release edges: no lock is not an error, a label mismatch refuses,
  and `--force` is the operator path.

## Resolutions

- Accepted: the MODIFIED requirement carries the whole new contract, and
  the usage scenario pins exit 64.
- Accepted: the refusal scenario carries the no-gh-call assertion.
- Accepted: one scenario per stale rule.
- Accepted: the release edges sit in the run-lock requirement.
- Rejected: surface tags, because the house spec files carry none for
  non-governed capabilities.

## Remaining Risks

- The scenarios pin behavior, not wording. The stderr text shape stays
  free until the implementation lands.
