# SCALE — this setup on a five-person team

The team: one product owner, two engineers, one QA engineer, one DevOps
engineer.

## Shared versus individual

**Shared, in the repository.** The spec flow in `openspec/`, the pipeline
skill, the gate tools, the hooks, and the agents are team property. One
change folder per feature holds the proposal, the design, the spec delta,
and the task list, so the team reviews intent before code. The quality
gates run in CI with the same commands as on a laptop, so a gate result
means the same thing to every person. The handover issues carry the
telemetry blocks, so the team reads one format after every merge.

**Individual, per person.** Each engineer keeps a personal scratch space:
the `.cc_logging/` directory, local worktrees, and personal memories. The
product owner works in the change folders and the dashboard, and runs no
gate tools. QA authors acceptance tests in the change folders and reads the
eval results and the scoreboard. DevOps owns the devcontainer, the floci
emulator, and the deploy skills, and reviews every registry change.

## What breaks first at team scale

**The one-writer spec flow breaks first.** Today one agent proposes a
change, and the same person approves it. Five people propose in parallel,
and two changes touch one capability without seeing each other. The fix:
one owner per capability folder, a rebase rule before a proposal merge, and
a nightly `openspec validate --all` job.

**The queue of hand-merged pull requests breaks second.** The discipline
gate holds one proposal merge at a time on `main`. With five people, the
merge queue becomes the bottleneck. The fix: smaller changes, and a merge
queue in CI.

**The registry becomes a conflict hotspot.** Every unit lands one line in
`tools/project_setup/registry.json`, and every new tool lands at the end of
the file. The fix: one directory per unit inside the registry, and a CI
check that the file stays sorted.
