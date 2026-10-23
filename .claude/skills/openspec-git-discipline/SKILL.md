---
name: openspec-git-discipline
description: Use when running OpenSpec propose, continue, apply, verify, archive, or worktree workflows where proposal artifacts, branches, merges, or archive timing affect git history.
license: MIT
compatibility: Requires git and OpenSpec workflow artifacts.
metadata:
  ported:
    from: intent-driven-dev/intent-driven-template
    commit: b5bda460a2180a55fc508fdedc4ef058d95355db
    license: MIT
---

# OpenSpec Git Discipline

## Core Rule

Every OpenSpec state change must cross `main` before the next lifecycle phase depends on it.

- Propose/continue artifacts may be drafted on a branch, but must be committed and merged to `main` before apply starts.
- Apply may run on `main`, a branch, or a worktree only if that exact proposal change is already available on `main`.
- Archive may run only from `main` after implementation is merged back.

Never create commits, branches, or merges outside the change the user approved. The user's approval of the task is the explicit ask this skill requires; the delivery pipeline owns the commit, branch, and merge steps.

## Gates

| Moment | Gate |
| --- | --- |
| Before propose | Prefer `main`; if not, warn and ask whether to continue intentionally. |
| During continue | Before creating the next artifact, commit the completed artifact changes, or state plainly that the work continues without that checkpoint. |
| After propose | Commit the proposal artifacts and open the proposal pull request for review. |
| Before apply | Confirm the proposal change is committed on `main`; then apply may run from `main`, a branch, or a worktree. |
| Before archive | Stop unless implementation is merged back to `main` and archive is running from `main`. |
| After archive | Commit the archive and spec sync changes through the archive pull request. |

## Required Checks

Before apply:

1. Run `git status --short`.
2. Verify `openspec/changes/<change>/` has no uncommitted proposal files.
3. Verify the proposal change exists on `main` before applying from any branch/worktree.

Use this language if the proposal has not reached `main`:

> I should not apply this yet because the proposal change has not reached `main`. A proposal can be drafted on a branch, but apply must start only after that proposal state is available on `main`. Please merge or commit the proposal to `main` first, then I can apply from `main`, a branch, or a worktree.

Before archive:

1. Run `git branch --show-current` and `git status --short`.
2. Stop if not on `main`.
3. Stop if implementation work has not been merged back to `main`.

Use this language:

> I should not archive this yet because archive must run from `main` after implementation is merged back. Verify makes a change eligible to merge; it does not replace the merge.

## Red Flags

- Applying a proposal that exists only on the current branch/worktree.
- Treating worktree visibility as proof that the proposal reached `main`.
- Creating the next continue artifact without asking about committing the previous one.
- Archiving from a feature branch or before implementation is merged to `main`.
- Committing, branching, or merging outside the approved change flow.

All of these mean: pause, explain the boundary, and ask the user to make the git state explicit.