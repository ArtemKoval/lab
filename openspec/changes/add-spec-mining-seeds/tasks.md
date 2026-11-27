# Tasks: add-spec-mining-seeds

## 1. The five capability deltas

- [x] 1.1 The `apple-fm` delta: the step ledger, the gates with one
  repair pass, the frozen contracts, and the local-only rule.
- [x] 1.2 The `knights-notebook-run` delta: the executed copy beside a
  clean source, the shim with its guidance, the package installs.
- [x] 1.3 The `notebooks` delta: the hermetic tests and the public
  checklist.
- [x] 1.4 The `project-setup` delta: the registry, the venv units, the
  interview, the doctors, and the backup-and-verify installer.
- [x] 1.5 The `spec-mining` delta: the report directory, the tree scan,
  the drift scan, the ranking, and the exit codes.

## 2. Gates and merge

- [ ] 2.1 `openspec validate add-spec-mining-seeds --type change
  --strict` passes.
- [ ] 2.2 `tools/spec_ste_check` passes on every artifact of this
  change.
- [ ] 2.3 The bridge regen runs after the last spec edit.
- [ ] 2.4 The root suite passes in the worktree. The environmental
  failures the memory notes record, counted at run time, do not count
  against this change.
- [ ] 2.5 The configs seed records its skip in the proposal, and the
  spec-references comment repeats it.
