# Design: port-crm-whole-tree-lint-fixes

## Cited lessons

- `worktree-shared-venv`: a fresh worktree has no `.venv`. The apply
  phase runs the crm suite with the main checkout interpreter at
  `crm/.venv/bin/python` from the worktree `crm/` directory.
- `mechanical-edit-verification`: one authority per identifier, and the
  suite arbitrates. Each ported fix lands as its own diff, and the crm
  suite arbitrates the result.
- `spec-ste-gate-scope`: the STE gate scans every `.md` under
  `openspec/changes/`. Every artifact of this change passes
  `tools/spec_ste_check` before the push.
- `process-issues-live-lock-vs-suite`: the loop lock is live in the
  primary checkout, so 7 scan tests fail there while the lock stands.
  The run reads those failures as lock effects, not regressions.

## Decisions

1. **Surgical port.** The upstream copy of `backend/main.py` also
   removes the `create_case` endpoint and its 3 imports. The issue
   names 9 pyright errors, and the endpoint removal is not one of
   them. It serves a different upstream milestone. The apply phase
   ports only the named fixes and keeps the endpoint.
2. **The None guards keep behavior.** `run_effect` raises 500 when the
   effect record is absent, and `HeldAward.outcome` falls back to
   `""`. Both paths cannot occur under the desk contract: the 404 and
   409 guards upstream of each read leave no None case the API can
   serve. One edge stays: a malformed pack whose `summarize` verb
   returns None turns a pydantic rejection into the `""` fallback.
   Pack manifests are reviewed artifacts under the `crm-domain-pack`
   contract, so the run accepts that edge in exchange for the honest
   response schema. The guards change no behavior the suite can see,
   so no crm delta carries them.
3. **The `award` removal restores the contract.** The backend model
   has no `award` field, and no caller passes one. The TypedDict is
   the agent client contract, so the extra field lies about it.
4. **Spec placement.** The `quality-gates` capability carries the
   repository delivery-gate contracts, and the crm gate list is one of
   them. The delta lands there. No new capability, because one
   requirement does not justify one.
5. **Test anchor.** The new requirement pins the crm-app skill text,
   because the skill is the surface the gate list lives on. The
   enforcing test reads the Gates section of
   `.claude/skills/crm-app/SKILL.md`, in the pattern of
   `tests/claude_infra/test_pipeline_rules.py`, and lands in
   `tests/crm_infra/test_crm_infra.py` beside the existing skill pins.

## Builder-check settles

The builder-check round raised 3 questions for the operator. This
section carries the answers the artifacts adopt, and the spec-gate
comment on issue 247 repeats them:

1. **In-flight crm changes.** The requirement binds from the archive
   merge of this change, per the OpenSpec sync semantics. A change
   that passed its propose phase before that merge keeps the gate
   list it proposed under.
2. **Mutator scope on this change.** The gate runs on the 2 changed
   product modules, `backend/main.py` and `backend/runs.py`, in the
   documented per-module shape. The guard lines alone are not a
   scope the mutator tool has.
3. **The kept `create_case` endpoint.** The next whole-file sync of
   `backend/main.py` from upstream meets the removal again. The port
   milestone that carries that sync owns the reconciliation, and the
   apply-phase handover issue records it as debt.

## Port manifest

| File | Fix | Upstream shape |
| --- | --- | --- |
| `crm/backend/tests/test_ported_refusals.py` | 7 imports to the top level | `replace`, `held`, `sign_off`, `loader` join the top imports |
| `crm/agent/api.py` | dead `award: float` out of `DecisionRequest` | one line down |
| `crm/backend/main.py` | `gated` payload type | `dict` becomes `dict | None` |
| `crm/backend/main.py` | `run_effect` None guard | 500 with a message, effect record returned |
| `crm/backend/runs.py` | `HeldAward.outcome` fallback | `outcome_line(...) or ""` |
| `crm/backend/tests/test_protocol.py` | importlib guards | 2 asserts before `module_from_spec` |
| `crm/backend/tests/test_scoreboard.py` | `RowMapping` cast | `cast(RowMapping, ...)` on `a_row` |
| `crm/agent/tests/test_screening.py` | lab-canonical pin, task 2.8 | the notebook machinery dies. The served text pins inline |
