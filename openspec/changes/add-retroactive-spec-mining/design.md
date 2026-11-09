# Design: add-retroactive-spec-mining

## Plan review

The inner-loop review examined the house tool template (`process_issues`,
`residue_scan`), the current spec corpus, the archive corpus, and the
dspy-gate bridge. The review settled these decisions:

- One read-only CLI produces one run directory per day. The three miners
  are pure functions over injected facts, so the tests stay hermetic. The
  CLI layer gathers the facts: the tree walk, the archive walk, and one
  `git log` call.
- The match rule stays mechanical. A unit name normalizes to kebab form and
  matches a capability directory name, or the committed data file supplies
  the alias or the coverage entry. No model and no heuristic text analysis
  sits in the tool.
- The unit classes in the default scan are the `tools/` directories, the
  hook scripts, the skills, and the projects. The name rule matches the
  exact capability names. The data file entries carry the units whose
  names differ, so the report does not drown in skill noise.
- The archive drift scan compares scenario names only, because names are
  the stable identity of a scenario in this corpus. The report guides a
  human, so a missed body edit stays a human question, not a gate.
- The data file is committed source, never generated. The report names the
  units the file does not know, so the operator extends the file when the
  tree grows.
- A same-day rerun replaces the files the run owns and leaves any other
  file in the run directory in place. The reports are reproducible from
  the repo state, so no run history is lost information.
- The exit contract follows the house shape: 0 on success, 2 on operational
  failure with the reason on stderr and an empty stdout. A missing root
  directory (`openspec/specs/`, the archive, or the git read) is an
  operational failure. `--json` switches the human report on stdout for
  one machine payload on the success path only.

## Context

The repo holds 31 capability spec directories, 33 archived changes, 18
tool directories, and 41 skills. The specs accrete per change. No
mechanical view names which live units lack coverage and which archived
deltas drifted. The dspy-gate bridge proves coverage for the governed set
only. The operator decides back-fills by hand today.

## Goals / Non-Goals

**Goals:**

- One opt-in command names the uncovered surface with evidence.
- One command reports the archive drift per capability.
- One command writes seed proposals that the propose flow can adopt.
- All three miners run hermetic and offline in tests.

**Non-Goals:**

- No LLM in the tool. Judgment stays with the model in the propose flow.
- No automatic change creation under `openspec/changes/`.
- No hook and no workflow wiring. Use is opt-in.
- No mutation into the saturation-pass owned-tools table. The table stays
  at nine entries.

## Decisions

### D1. Package shape follows the house template

`tools/spec_mining/spec_mining/` holds `__init__.py`, `__main__.py`,
`cli.py`, and `core.py`. `pyproject.toml`, `ruff.toml`, and `README.md`
sit at `tools/spec_mining/`. The CLI takes one injectable runner for the
git and filesystem facts, so tests inject canned facts and no network or
real git runs. Alternatives: a single-file tool like `sec_scan` loses the
room for three miners. A `reports/` import coupling to `dspy_gate` would
couple two tools. The house package shape won.

### D2. One committed data file carries the aliases and the coverage

`tools/spec_mining/spec_mining/units.json` holds three maps:

- `aliases`: unit path to capability name for the units whose names differ
  from the capability name. Example: `tools/spec_ste_check` maps to
  `spec-ste-enforcement`. Hook keys drop the `.sh` suffix.
- `projects`: one project directory to its capability set. A set entry can
  carry one glob with a trailing `*`. Example: `crm` maps to `crm-*`.
- `coverage`: explicit entries for units whose coverage no name rule
  finds. The skills enter here.

The name rule normalizes a unit name to one lowercase kebab token: it
strips the extension, turns each `_` into a `-`, and collapses repeated
dashes. Every class follows the name rule first. The data file entries
cover the units whose names differ from their capability. A skill or a
project with neither a name match nor an entry reports as uncovered. A
data-file entry whose unit left the tree surfaces in one stale-entries
section. Alternatives: a full explicit inventory for every unit gives
exact numbers but rots fastest. A data-file-only rule hides the exact
name matches of the skills. The name rule plus the data file keeps the
file small and the report sharp.

### D3. The drift scan compares scenario names

The drift scan parses `#### Scenario: <name>` lines from the `ADDED` and
`MODIFIED` sections of each archived delta and from each capability spec
with a local regex. It reports the archived scenario names the capability
spec lost. An archived scenario whose capability spec directory does not
exist reports as drift with one missing-spec mark. The `REMOVED` and
`RENAMED` delta sections stay out, because a removed scenario left the
spec on purpose and a rename keeps the new name in the body text.
Alternatives: importing the dspy-gate scenario parser couples two tools.
A full body compare makes every wording edit a drift entry. The name
compare won.

### D4. The history ranking counts one bounded git log

One `git log --name-only --format=%H` call over `main` feeds a count per
uncovered area. The area of a unit is its repo-relative path, so the
scenario granularity of the spec holds. Ties order by area name in
ascending order. No pagination and no per-area calls. Alternatives:
`shortlog` hides the path counts. A first-path-segment area merges all
tools into one rank. The per-unit call won.

### D5. Seeds are scaffolds, not changes

A seed holds the mined evidence: the uncovered units, their commit counts,
and the drift entries for the candidate capability. The candidate name is
the kebab form of the unit name. The seed text is a scaffold. The propose
flow with the user approval rewrites it into a real change. The STE gate
runs when the text enters `openspec/changes/`, because seeds live outside
the hook scope. Alternatives: writing partial changes under
`openspec/changes/` puts half-formed artifacts inside the planning home.
The staged seed won.

### D6. The report layout is stable

A run writes `reports/spec_mining/<UTC-date>/` with `coverage.json` (one
payload with the tree, drift, and ranking sections), `report.md` (the
human summary), and `drafts/`. The date is the ISO `YYYY-MM-DD` form in
UTC. A same-day rerun replaces the files the run owns and leaves any other
file in the directory in place, so a hand-written note survives.
Alternatives: timestamped run dirs accumulate residue, and a wholesale
directory replace deletes files the run never wrote. The owned-files
replace won.

### D7. The interpreter follows the house fallback

The commands use the shared venv python when it exists and the system
`python3` after that. The package needs only the stdlib, so the fallback
runs it unchanged.

## Structure

The diagram is lightweight C4-inspired, ASCII, per house design precedent.
It shows the container and its components with the reads and the writes.

```text
+------------------------------------------------------------------+
| spec_mining run                                                   |
|                                                                   |
|  tree scan         archive drift       history ranking            |
|  (unit names       (delta scenario     (git log counts per        |
|   vs specs dirs)    names vs spec       uncovered area)           |
|                     scenario names)                               |
|       |                 |                     |                   |
|       +--------+--------+----------+----------+                   |
|                v                   v                              |
|         report build           seed build                         |
|         (core.py)              (core.py)                          |
|                |                   |                              |
|                +---------+---------+                              |
|                          v                                        |
|              reports/spec_mining/<UTC-date>/                      |
|              coverage.json report.md drafts/                      |
+------+------------------------------------------------------------+
       | reads                          | writes
       v                                v
  openspec/specs/                reports/spec_mining/ (only here)
  openspec/changes/archive/
  working tree, git log
  units.json data file
```

Boundaries, responsibilities, and assumptions:

- One container: the CLI. The three miners and the two builders are
  components inside it. No service boundary and no queue exists.
- The reads are local files and one local `git log`. The writes land in one
  directory. The boundary is the trust boundary for the read-only claim.
- The data file is source, not state. The operator owns its entries.
- Assumption: scenario names are unique per capability, because the specs
  use one `#### Scenario:` heading per name.
- Open question: none at the container level.

## Risks / Trade-offs

- [The data file rots as the tree grows] -> The report names the unknown
  units in their own section, so the operator sees the gap and extends the
  file.
- [A same-day rerun overwrites the morning report] -> The reports are
  reproducible from the repo state, so the overwrite loses nothing.
- [Scenario name compare misses body drift] -> The drift list guides a
  human review, so the missed body edit stays visible at propose time.
- [The seed text bypasses the STE hook] -> The skill mandates the STE gate
  run when a seed enters `openspec/changes/`.
- [The name rule renames silently when a tool moves] -> The unknown-units
  section of the report exposes the rename.

## Migration Plan

New tool. No migration. The rollback deletes `tools/spec_mining/`,
`tests/spec_mining/`, the skill, and the run directories. No other
component reads the run output.

## Open Questions

- The CI coverage wiring lands at apply time. The package joins the
  coverage source and the root suite, per the proposal Impact.
- The saturation ratchet stays out for this tool by precedent. A future
  change can revisit the owned-tools table.

## Spec delta

One new capability, `spec-mining`, with five requirements: the tree scan,
the archive drift scan, the history ranking, the run output, and the CLI
contract.
