# 0018 - Library assignment history discipline

- Status: accepted
- Date: 2026-10-31
- Ported from: ArtemKoval/library_crm adr/0010 (2026-10-31), renumbered
  because the lab ledger owns 0010 through 0017. The decision binds the
  pull requests of the library assignment in that repository.

## Context

The library assignment (issue
[ArtemKoval/library_crm#1](https://github.com/ArtemKoval/library_crm/issues/1))
sets its own ground rules for git history: small commits, meaningful
messages, and no squashing or rewriting. The repository convention in
CLAUDE.md and the feature-pipeline skill is a squash merge per pull
request, then branch deletion. A squash merge replaces the small commits of
a feature branch with one commit, and the assignment grades the history.
The two rules conflict for every pull request of this assignment.

## Decision

For the pull requests of the library assignment, `main` takes a merge
commit instead of a squash merge. Each feature branch keeps its small,
atomic commits with conventional subjects and proof-of-work bodies. Branch
deletion after the merge stays in force, and the openspec-git-discipline
gates stay in force: the proposal pull request merges before
implementation, and the implementation pull request merges before the
archive pull request.

This decision covers the pull requests of this assignment only. Work that
does not carry the assignment returns to the squash merge convention.

## Consequences

The mainline history shows one merge commit per pull request, with the
small commits of the branch under it. `git log` reads as the assignment
expects, and every walkthrough question about "why the agent did what it
did" finds the commit that did it. The cost is a busier mainline graph and
merge-commit noise that the squash convention avoided. A reviewer who
wants one-commit-per-feature reads the merge commit subject line.
