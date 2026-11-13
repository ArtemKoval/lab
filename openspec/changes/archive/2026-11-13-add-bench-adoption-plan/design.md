# Design: add-bench-adoption-plan

## The analysis

Bench (`github.com/ed-donner/bench`) is a four-app teaching monorepo.
Its harness is the layer around the apps: one entry document, three
short role documents, one pre-handover command, a controls table, a
Stop-hook backstop, and a gate that only CI holds. The element map
below compares each piece against this repository and gives the
verdict.

| Bench element | This repository today | Verdict |
| --- | --- | --- |
| `AGENTS.md` entry with golden rules | CLAUDE.md plus the charter hook | Partial. The golden rules exist in the charter. The short-entry shape does not. |
| Role-split docs: PROCESS, STANDARDS, CONTROLS | One CLAUDE.md, the pipeline skill, the charter | Partial. The split keeps each document short enough to read per task. |
| One pre-handover command (`npm run check`) | Discrete gate commands in the pipeline skill text | Adopt. One local entry over the changed paths removes the reading tax. |
| Controls-layers table: gate vs backstop per layer | Implicit in the charter and CLAUDE.md | Adopt. One table names the truth for every gate. |
| Stop-hook lint backstop, one block per session, failures handed back | No Stop hook | Adopt as a proposal. The pattern (a per-session marker, one block, then relent) is sound and cheap. |
| knip: unused files, exports, dependencies | dead_export_scan covers dead exports | Partial. Unused dependencies stay outside. A low-priority extension. |
| jscpd duplication, advisory | dryer gates duplication at 0.8 | Skip. This repository is stricter. |
| gitleaks plus a PII secrets gate | sec_scan over tree, history, and diffs | Skip. Covered. |
| lefthook pre-commit | The pipeline gates run before the push | Skip. A pre-commit hook duplicates the pipeline bar. |
| SPEC-to-PLAN flow | OpenSpec propose with the approval gate | Skip. Covered. |
| Strict type-aware lint, a11y, sonarjs | ruff with the house config | Skip. Language-specific. |
| Three test layers, browser verification | Unit, contract, e2e lanes | Skip. Covered. No browser surface. |

Deliberate differences this plan rejects: bench forbids the agent
from pushing, and its gate is CI alone. This repository grants the
loop the automation authority (ADR 0012) and keeps the local suite as
the merge bar, so the bench rules do not transfer.

## The adoption candidates

1. **The single local entry.** One command that runs the fast gates
   over the changed paths: the scoped suite, ruff, and the STE gate.
   Future change: `add-check-entry`.
2. **The controls-layers table.** One table in CLAUDE.md that names,
   for every gate this repository runs, whether it gates or backs up.
   Future change: `add-controls-table`.
3. **The Stop-hook backstop.** A Stop hook that runs the fast gates
   on turn end, blocks once per session through a per-session
   marker, hands the failures back, and relents. The bench
   implementation caps the cost at one extra turn and hands the
   linter's own messages back. Future change:
   `add-stop-backstop`, with its own peak-hours and budget analysis.

## Edge cases and risks

- The Stop hook runs on every turn end, so its command stays inside
  a few seconds. The fast gates scope to changed paths only.
- The one-block marker lives in the temp directory keyed on the
  session id, the pattern bench proven in its own hook.
- The controls table goes stale when a gate lands without the table
  row. The table change adds the row duty to the pipeline's gate
  steps.

## Verification

The artifacts carry the plan. No code ships here. The strict
validate and the STE gate pass on the change directory. The three
adoption candidates become issues or changes of their own when the
operator orders them.
