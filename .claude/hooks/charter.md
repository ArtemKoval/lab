# Harness charter

You run inside the lab repository of Art Koval. This charter holds the
contract that must survive compaction. CLAUDE.md is the source of truth
for conventions. The feature-pipeline skill owns the delivery flow.

## Delivery contract

Every repository change passes through the feature-pipeline skill.
Purely informational requests change nothing and skip it. Isolate each
change on a type-prefixed branch. Never work on the mainline.

OpenSpec governs behavior. Artifacts live under openspec/. The proposal
artifacts merge to main before implementation starts. Implementation
merges before the archive runs. The openspec-git-discipline skill owns
these gates. Durable decisions go to adr/ as immutable records.

## Quality gates

Run the full hermetic suite before you claim a green run. The gates are
coverage, complexity, and mutation: 100 percent line and branch coverage
of new code, cyclomatic complexity of 10 or lower, and a mutation score
of 95 percent or higher on changed code. Mutate an out-of-tree copy,
never the repository. Nothing proceeds on red.

## Skills first

Examine the skill list before you act. If a skill covers the task, use
it. Process skills come first: grill-me for unclear requests,
systematic-debugging for defects, test-driven-development for code,
verification-before-completion before any success claim. Review rounds
use the adversarial pair: adversarial-author drafts, adversarial-reviewer
challenges. Name the model on each agent dispatch when the harness
allows it. Give the final whole-diff review to the strongest model.

## Review and merge discipline

Verify each review finding before you implement it. Push back with
technical reasons when a finding is wrong. No performative agreement.
Clarify every unclear item before you fix any item. Reply in the review
thread, not as a top-level comment. Destroy work only after the user
types discard. Remove only worktrees this pipeline created.

## Worktrees

An agent or a team of agents works on a feature branch inside its own
worktree. In Claude Code, use the EnterWorktree tool. Outside Claude
Code, use git worktree add. After the merge, delete the branch, remove
the worktree, and resync the mainline.
