---
description: Work one unit of work of the library domain change end to end: brief, test first, gates, atomic commit, ledger
argument-hint: "[task id or keyword from tasks.md]"
---

# One unit of work on the library domain

Drive exactly one unit of work from `openspec/changes/add-library-domain/tasks.md`.
Match the unit with: $ARGUMENTS

Follow this flow in order, and stop after the commit:

1. **Brief.** From the repository root, run
   `tools/zai_routing_audit/.venv/bin/python -m plan_exec brief --plan openspec/changes/add-library-domain/tasks.md --task <id> --out .plan_exec/add-library-domain`
   to write the brief for this unit. Read the brief and the files it names.
   Read the nearest lessons first: CLAUDE.md, the relevant skill, and the
   memory notes.
2. **Test first.** Write the test that proves the unit, and run it to see
   it fail for the right reason. The suite runs from `crm/` with
   `uv run pytest <test-file> -q`.
3. **Implement.** Write the smallest code that passes the test. Keep every
   function at cyclomatic complexity 10 or less. Stay inside the pack
   folder. Never edit engine code: `crm/backend/`, `crm/agent/`,
   `crm/context/`, `crm/domains/loader.py`, `crm/validate.py`,
   `crm/smoke.py`.
4. **Gates.** Run, and make each one green before you go on:
   - `crm/.venv/bin/python -m pytest` (the touched suite, then the full one)
   - coverage of the new code at 100 percent lines and branches
   - `tools/crapper/crapper --threshold 10 --changed`
   - `tools/dryer/dryer --threshold 0.8 --fail-above --changed`
   - `tools/mutator/mutator --changed` (mutate an out-of-tree copy)
   - `cd crm && uv run python validate.py library` for pack files
5. **Commit.** One atomic commit per unit. The subject is a conventional
   commit line. The body states what changed, why, and how you proved it.
   Never stage a file the unit does not own.
6. **Ledger.** Tick the task in `tasks.md`, and append the ledger line:
   `tools/zai_routing_audit/.venv/bin/python -m plan_exec ledger --plan openspec/changes/add-library-domain/tasks.md --dir .plan_exec/add-library-domain complete --task <id> --tests "<the gate command>" --result "<the observed result>"`.

Report at the end: the unit id, the diff stat, the gate results, and the
commit hash. If a gate stays red after two driven rounds, stop, and write
the blocker in the ledger instead of a weak fix.
