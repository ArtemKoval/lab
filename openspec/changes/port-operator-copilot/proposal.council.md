# Council Notes: proposal.md

## Author Summary

The proposal ports the `operator-copilot` prototype into the lab as the
fifth crm domain pack: the `garage` pack with money awards, the 600 pound
sign-off limit, the routing rules as pack policy, the seed cases from the
source demo calls, and no prototype code carried over. The source
repository stays untouched as the archive, and the delivery lands as clean
port commits on one squash-merged pull request.

## Reviewer Challenges

- The Impact list omitted the `crm/playwright.config.ts` edit that the e2e
  requirement needs, and the file count of about 20 sat under the real tree
  of about 30 files.
- The routing sentence ran past the 20 word procedural limit.
- The seed list fused the Leeds Nissan Leaf case with the Tesla
  charging-fault case of the source transcript.

## Resolutions

- Accepted: the Impact list names the playwright config edit, and the file
  count reads about 30.
- Accepted: the routing sentence is split, and the seed list names the two
  EV cases separately.

## Remaining Risks

- The capacity planner of the source stays a follow-up with its own
  proposal, recorded in the handover issue.
