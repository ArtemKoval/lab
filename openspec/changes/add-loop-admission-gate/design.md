# Design: add-loop-admission-gate

## Source

The requirement is proposal P3 of the dsh analysis. The adversarial pair
folded two blockers and five fixes into the artifacts: the gh author
shape is an object and the code reads `author.login` with the field-list
pins on both fetches, the config row touches four surfaces beyond the
code, the refusal precedence carries the fail-closed observables instead
of an identical-outcome claim, the `-bot` suffix is cut, and the
admission predicate stays pure in `core.py` with the config read in the
CLI.

## Plan review

- The refusal sits above the label precedence, and the reason is
  fail-closed observables, not an identical outcome. The `--json` state
  and action differ from skip, the plain column prints refused, and the
  entry carries the author. A foreign `human-approved` issue with
  artifacts classifies as apply today, so the loop would fold stranger
  content into the apply phase.
- The gh author shape is an object with a `login` key. The fetch asks
  for the top-level `author` field, and the extraction reads
  `author.login`, with argv pins on both fetches so a forgotten field
  cannot produce a silent full refusal.
- The `-bot` suffix is cut. The report pins only `[bot]`, and `-bot`
  can override an explicit operator grant, because a human login can
  end in `-bot` (a person named RenovateBot). Real automation carries
  `[bot]` in the API login.
- The config failure is exit 2, not exit 3. The file ships in the
  clone, so its absence is a broken deployment, and a restart repairs
  it only when the clone repairs. The note names the config path.
- The admission predicate stays pure in `core.py` over the login, the
  allowed set, and the bot suffix, and the config read and path
  resolution stay in the CLI layer through one injectable path
  constant, so the tests point it at a fixture file.
- The status changes keep its spec sentence true: the fetch gains the
  author field, the blocked test applies the admission gate through the
  same predicate, and the config row sits between the auth row and the
  issue-list row with the level `config`. The payload keys and the
  first-match order survive, and the unreachable-component null rules
  survive.
- The loop account gets no special entry. The operator entry admits the
  handover-filing account. A future bot-login loop account stays
  refused with no code change, and its handover issues report refused
  with action none, so the loop-touches-nothing invariant survives.

## Diagrams

Format: ASCII in fenced blocks. Rigor: lightweight C4-inspired,
following the house precedent.

### Container diagram

```text
+-------------------------------------------------------------------+
| the scan run                                                      |
|                                                                   |
|  lock examine --> config read --> gh issue list --> gate walk     |
|                        |              |               |           |
|                        v              v               v           |
|  +---------------------+   +---------------------+   +---------+  |
|  | authors.json at     |   | gh (issues with     |   | refused |  |
|  | the module path     |   | author objects)     |   | above   |  |
|  +---------------------+   +---------------------+   | every   |  |
|                                                      | label   |  |
|  +---------------------------------------+           | state   |  |
|  | status: halt, auth, config, list,     |           +---------+  |
|  | blocked (gate first), lock            |                        |
|  +---------------------------------------+                        |
+-------------------------------------------------------------------+
```

### Component view

```text
+----------------------------------------------------------------+
| tools/process_issues/process_issues/                           |
|                                                                |
|  core.py     STATE_REFUSED + the pure admission predicate      |
|              over the login, the allowed set, and the suffix   |
|  authors.py  the path constant, the load, the shape validation |
|  authors.json the operator list                                |
|  cli.py      the author field in both fetches, the config      |
|              read, the gate in the queue walk, the status      |
|              config row and refusal in the blocked test        |
+----------------------------------------------------------------+
```

## Decisions

1. The admission predicate `admitted(login, allowed)` in `core.py`
   returns True only when the login is a nonempty string that is in the
   case-insensitive allowed set and whose lowercase form does not end
   with `[bot]`. A None login or an absent author object refuses.
   Rationale: the predicate stays pure and total, and every refusal
   path is explicit.
2. The config module `authors.py` carries the module-relative path
   constant, the load, and the shape validation. The required shape is
   `{"allowed_authors": [str, ...]}` with extra top-level keys ignored,
   and an empty list is valid and refuses everyone. The CLI resolves
   the path through the constant, and the tests monkeypatch it to a
   fixture file. Rationale: hermetic tests and a worktree-proof path.
3. The config failure is exit 2 with one stderr note that names the
   path. The file ships in the clone, so its absence is a broken
   deployment, and a restart repairs it only when the clone repairs.
   Exit 3 means missing operator setup, and a shipped file that went
   missing is not setup. Rationale: the dsh line stays exact.
4. The refusal sits above the label precedence as a pre-check in the
   queue walk, before `classify`, and `state_for_labels` stays
   label-only. The refusal carries fail-closed observables: the state
   and action strings, the plain column, and the author key. Rationale:
   a stranger cannot set labels, so a foreign issue with operator
   labels got them from the operator, and refused tells the operator
   more than skip.
5. Both fetches gain the `author` field, and the queue and the status
   blocked walk read `author.login` with a None object refusing. Tests
   pin the argv field lists of both fetches, because a forgotten field
   produces a silent full refusal. Rationale: the silent-refusal
   failure mode has no other detector.
6. The status config row sits between the auth row and the issue-list
   row with the level `config` and exit 2, and the blocked test applies
   the predicate before the label walk. Rationale: the spec sentence
   "the blocked detection reuses the scan classification" stays true,
   and a stranger cannot page the operator through status.
7. The recipe needs no new step. A config fault is an exit-2 component
   error, and the recipe already stops and reports on that category.
   The skill and README texts gain the new row, the payload key, the
   refusal rule, and the list edit path. Rationale: one action table
   serves the new exit source.

8. The registry carries no new unit, because the config ships inside
   the existing process_issues unit directory. The list stays
   code-tracked and edits through pull requests.

## Builder settlements

The builder pass settled the remaining gaps. The config module carries
`AUTHORS_PATH` and `load_authors()`, with one exception type that names
the path, and the loader returns the validated raw string list while
the predicate lowercases both sides. The wrong-shape enumeration is the
missing file, the unparsable JSON, the non-object top level, the
missing key, the non-list value, and the non-string item. The author
extraction folds an absent author, a null author, and a non-string
login into a None login before the predicate. The fixture rule gives
every queue and status fixture an admitted `author` object, and the
refusal and null-author cases gain new fixtures. Status loads the
config once, and the config row and the blocked walk share the result,
with the row order keeping a broken config ahead of the walk. The
shipped list carries exactly the operator login, because no second
account files issues on this repository.

## Failure modes

- A forgotten `author` field in either fetch produces a silent full
  refusal at exit 0. The argv pins are the detector.
- A null author on a real issue is real: GitHub renders a deleted
  account with no author object. Fail-closed refuse, and the payload
  carries null.
- A letter-case rename of the operator login would silently refuse the
  operator. The case-insensitive comparison absorbs it.
- An issue flood can hide older operator issues behind the 200-issue
  fetch window. The scan and status carry the same bound, and a later
  change can raise or filter it.
- The gate covers issue authors only. A foreign pull request with a
  `Refs #NN` line stays outside this change, and the residue of a
  foreign PR stays in the residue scan's scope, not the scan's.

## Entropy (ASIT)

- Unification: the predicate, the config module, the fetch field, and
  the status row reuse the house seams. No new component kind beyond
  one config module and one JSON file.
- Division: the pure predicate in `core.py`, the config read at the CLI
  edge, and the refusal pre-check in the queue walk.
- Breaking symmetry: the refusal sits above every label state, and the
  config row sits between the auth row and the list row.
- Object removal: no nonhuman list, no per-source cells, no gh bot
  field reliance. The recipe needs no new step.
- No new dependency.
