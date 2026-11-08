# Analysis: saturation testing for the harness — what issue 123 asks and what the measurement found

- Issue: ArtemKoval/lab#123
- Source: the X post at
  `https://x.com/unclebobmartin/status/2118697589021315083`, with the
  provenance note in section 1
- Date: 2026-11-08
- Status: analysis with a measurement. The adoption proposals in
  section 6 need approval. Each one becomes a separate change with its
  own review.

## 1. Scope

This run pins the saturation-testing definition against the tools this
repository vendors, measures the saturation of two owned tools with
full mutation passes, and lists adoption proposals in value order. The
X post sits behind a login wall, so the definition comes from search
summaries of the post and from the mutation-testing post at
blog.cleancoder.com from June 2016. The measurement ran once on this
host, with 4 CPU cores, on repository state at main after PR 148.

## 2. What saturation testing is

Robert C. Martin uses saturation testing as the name for
mutation-driven test adequacy. A mutation tool changes one operator or
one constant at a time and runs the test suite. A mutant that survives
marks a missing assertion. The suite is saturated when no mutant
survives. His post names two tools: crapper and mutator. This
repository vendors both, at pinned commits, under `tools/`. The mutator
prints a score of killed over killed plus survived, and it exits 3
when a survivor exists. Under this definition, the saturation bar is
exit 0 on the full surface, not a percentage.

## 3. What the repository already covers

The quality gates run the mutator on the changed paths of every pull
request, at 4 workers, with the suite of the touched area. The local
pipeline rule demands zero survivors on added or modified code. CI
resolves a score of 95 percent or more as a pass. ADR 0005 accepted
the three vendored tools as the default gates and rejected whole-tree
mutation in CI, because the runtime is unbounded. The coverage floor
sits at 100 percent line and branch coverage on the owned tools. The
gap the definition exposes: the gate sees the diff, so the saturation
of the whole harness surface was unknown before this measurement.

## 4. The measurement

One coverage pass covered both tools and their suites. A scan pass
counted the sites first, and the projection from the anchor rate of
about 48 mutants per minute sat far under the 60-minute budget, so no
per-module split ran. Each full pass finished inside one 10-minute
command window.

| Tool | Sites | Killed | Survived | Timeouts | Uncovered | Score | Exit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `tools/process_issues` | 187 | 184 | 0 | 3 | 0 | 100.0 | 0 |
| `tools/spec_ste_check` | 67 | 65 | 1 | 1 | 0 | 98.5 | 3 |

The per-module table:

| Module | Sites | Score | Survivors |
| --- | --- | --- | --- |
| `process_issues.authors` | 6 | 100.0 | none |
| `process_issues.cli` | 77 | 100.0 | none |
| `process_issues.core` | 14 | 100.0 | none |
| `process_issues.ledger` | 16 | 100.0 | none |
| `process_issues.lock` | 65 | 100.0 | none |
| `process_issues.status` | 6 | 100.0 | none |
| `spec_ste_check.cli` | 11 | 100.0 | none |
| `spec_ste_check.hook` | 33 | 100.0 | none |
| `spec_ste_check.rules` | 21 | 95.5 | 1 |

The three timeouts on `process_issues` count as killed, because a hung
mutant is a detected mutant. The one survivor sits in
`spec_ste_check.rules`, in the form `check_tenses`: the mutation
deletes the `-` of the `[-1]` index that takes the last word of a
progressive match. Every test progressive in the suite carries two
words, where `words[-1]` and `words[1]` are the same string, so the
mutant survives. A test with a three-word progressive, such as `has
been running`, kills it. The survivor is a missing assertion, and the
module is not saturated.

## 5. What a saturation practice adds

The changed-paths gate and the saturation bar differ in three ways.
First, scope: the gate sees the diff, and the saturation run sees the
whole module list. This measurement found the `check_tenses` gap
exactly because the pass left the diff. Second, the bar: CI resolves
95 percent as a pass, while the saturation bar is exit 0. The loop
engine passed at exit 0 today. The checker did not. Third, cadence:
the gate runs per pull request, and a saturation pass runs when the
surface moves or on a schedule. A whole-repo ratchet would record the
per-module score after each pass and refuse a drop. A saturation curve
per module would show the score over time and expose the modules where
tests stop paying. The CI cost of a full pass over both measured tools
stayed under 10 minutes at 4 workers. The whole harness, at ten tools
and this rate, projects under one hour, which ADR 0005 rejected for
pull requests but which fits a scheduled pass outside them.

## 6. Proposals in value order

1. **Kill the one survivor.** Add a three-word progressive case to the
   `spec_ste_check` tests, rerun the full pass, and record exit 0. Low
   cost, and it lifts the checker to the saturation bar. Own change.
2. **A scheduled saturation pass with a ratchet.** Run the full pass
   over the owned tools on a schedule, store the per-module scores,
   and refuse a drop. The snapshot store and the schedule are decisions
   for that change, and any CI placement must answer the ADR 0005
   rejection in its own ADR.
3. **Close the 95-percent gap.** Decide whether CI keeps the
   percentage resolution or rises to exit 0 on the changed paths. The
   loop engine already meets exit 0, and the checker misses it by one
   known survivor, so the gap is small today.
4. **Extend the measurement to the remaining owned tools.** The sample
   here is two of ten tools. The same command shape measures one tool
   per run, and the proposals above stay ahead of it in value.

## 7. Summary

The loop engine is saturated today: 187 sites, zero survivors. The
checker misses the bar by one known mutant with a known fix. The
saturation definition fits the vendored tools exactly, because the
tools are the tools the definition names. The next actions, in value
order, sit in section 6, and each one waits for its own approval.

## 8. Correction, 2026-11-08

The proposal 1 mechanism cannot kill the survivor. The progressive
regex at `rules.py:49` matches one auxiliary word and one `-ing` word,
so every match carries two tokens. The sentence `has been running`
matches `been running`, and the two indices agree for every input. No
test can kill that mutant under this tool's operator set. The change
that reaches exit 0 captures the participle in the regex and reads
`match.group(1)`. Line 191 held three sites before the change and one
after, so the tool total moves from 67 to 65 sites. The new `1 -> 0`
site at `rules.py:191` dies through the existing allowlist test. The
full pass on this host, with the manual coverage pass from the quality
gates, records 65 sites, 64 killed, no survivors, and exit 0. One site
at `cli.py:62` stays uncovered in that pass, because the manual
coverage pass misses the subprocess that hits it.
