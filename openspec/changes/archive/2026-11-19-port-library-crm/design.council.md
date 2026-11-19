# Council Notes: design.md

## Author Summary

The design was drafted by the primary agent during the z.ai peak window.
The reviewer subagent challenged it against the repository facts and the
scratch merge clone.

## Reviewer Challenges

- The design under-specified the compose resolution and claimed a lab
  loopback database that does not exist. The db service is new through the
  port, and no test pins the binding contract. (CONFIRMED)
- The plan applied the child's live spec files in the implementation while
  the change deltas carry the same content, which collides with the archive
  sync discipline. (CONFIRMED)
- The three new-capability deltas lost the child Purpose sections that the
  archive flow copies into the live specs. (CONFIRMED)
- No artifact inventoried the merged diff against the gate-integrity
  protected set. (PLAUSIBLE, then verified)
- The merge report had no stable home and no deletions row. (CONFIRMED)
- The task list named prettier and the design did not. (CONFIRMED)
- The 10k-line mutation estimate was unexamined. (PLAUSIBLE, then measured)
- The slidecast conftest switches its import root on `MUTANT_UNDER_TEST`,
  so the out-of-tree mutator copy must mirror the repository layout.
  (CONFIRMED)

## Resolutions

- Accepted: the compose decision now builds the db service from the fork
  facts, binds it to the loopback in the base, publishes it through the
  override, and pins the contract with a compose test.
- Accepted: the applied merge excludes `openspec/specs/`, so the archive
  applies the deltas as the only spec mechanism. The hand-resolved
  conflicts drop from 7 to 6.
- Accepted: the three deltas carry the child Purpose sections verbatim.
- Accepted and verified: the protected-set inventory names exactly one hit,
  `tests/slidecast/conftest.py`, a new test conftest. The pull request
  carries the acknowledgment line at creation, and the operator merge
  acknowledges it under the full-delivery approval.
- Accepted: the port script writes the merge report with a deletions row to
  `reports/port_library_crm/`.
- Accepted: the design names all four dashboard gates.
- Accepted and measured: the mutation surface is 5059 production Python
  lines, with 4435 test lines.
- Accepted: the mirror-layout requirement joined the gate-scope decision
  and task 2.9.

## Remaining Risks

- The desk and resolution fixtures may need edits in the evolved
  `crm/conftest.py`. The suite run decides.
- The e2e lane depends on the host stack. A skip lands in the pull request
  body when the stack is absent.
