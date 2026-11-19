# Council Notes: proposal.md

## Author Summary

The proposal was drafted by the primary agent during the z.ai peak window,
per the operator's timing decision. No separate author subagent round ran.
The reviewer subagent challenged the draft against the child clone, the lab
tree, and the scratch merge clone.

## Reviewer Challenges

- The engine-feature list named a resolution archive state that exists in
  no child file. (CONFIRMED)
- The compose story claimed the base keeps a loopback database, but the lab
  compose carries no db service at all. (CONFIRMED)
- The Impact line omitted `crm/docs/`, and the ADR port read as future work
  although the records already sit on the branch. (CONFIRMED)
- The commit count and the 154/71/7 split needed re-verification before the
  pull request repeats them. (PLAUSIBLE)
- The merge deletion set was unexamined. (PLAUSIBLE)

## Resolutions

- Accepted: the phantom became the issued-state semantics from the child's
  crm-engine requirements. Verified by search: no `archiv` match in the
  child tree.
- Accepted: the compose facts are now in the design. The fork base carried
  only the emulator, the lab added Langfuse, the child added the db
  service.
- Accepted: `crm/docs/` joined Impact, and the ADR bullet states the
  records landed on the branch.
- Accepted and verified: 68 commits, 154 added files, 78 child-modified
  files with 7 also touched by lab. The numbers hold.
- Accepted and verified: the child diff carries only additions and
  modifications, so the deletion set is empty.

## Remaining Risks

- The pull request body repeats only numbers this change verified. The
  handover issue repeats them from the merge report.
