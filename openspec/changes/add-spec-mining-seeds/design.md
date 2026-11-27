# Design: add-spec-mining-seeds

## Cited lessons

- `worktree-shared-venv`: the worktree has no venvs. The gate runs use
  the main checkout interpreters by absolute path.
- `spec-ste-gate-scope`: the STE gate scans every `.md` under the
  change dir. Every artifact passes `tools/spec_ste_check` before the
  push.
- `mechanical-edit-verification`: one authority per identifier. Each
  requirement derives from the surface's own README or code, and the
  strict validator arbitrates the text.

## Decisions

1. **Five converts, one skip.** The six seeds split by what the
   surfaces can honestly pin. `configs/wezterm` configures a terminal,
   but no suite exercises it and no scenario is testable today, so its
   conversion records a skip on that basis, not a spec. The other
   five surfaces carry real behavior the suites already exercise.
2. **One change, five deltas.** The skill's flow names one candidate
   per propose, picked with the user. Issue 265 aggregates the six,
   and the loop carries one change per issue. The gate reviews the
   batch. The fold removes one delta file per rejected capability,
   and the other deltas stand.
3. **The capabilities carry the seed names where the seed named the
   behavior**, and the behavior-named form where it aids the reader:
   the `apple` seed converts as `apple-fm`, because the surface lives
   at `apple/fm/`.
4. **Spec-only change.** The deltas pin behavior the existing suites
   already exercise: `tests/notebooks/` pins the notebook tests, the
   setup completeness test pins the doctor contract, and the
   spec-mining suite pins the tool. The apply phase carries no
   implementation tasks.
5. **The strict validator arbitrates the text.** The STE gate and
   `openspec validate --strict` pass on every artifact before the
   push.

## Surface map

| Seed | Surface | Capability | Verdict |
| --- | --- | --- | --- |
| add-apple | `apple/fm/simple_game` | `apple-fm` | convert |
| add-configs | `configs/wezterm` | none | skip, no behavior contract |
| add-knights-notebook-run | `tools/knights_notebook_run` | `knights-notebook-run` | convert |
| add-notebooks | `notebooks/` + `tests/notebooks/` | `notebooks` | convert |
| add-project-setup | `tools/project_setup` + the doctors + the skill | `project-setup` | convert |
| add-spec-mining | `tools/spec_mining` + the skill | `spec-mining` | convert |
