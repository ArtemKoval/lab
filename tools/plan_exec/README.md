# plan_exec

A stdlib CLI for long plan-execution runs. It extracts one task as a
brief, packages a commit range for review, and keeps an append-only
ledger that survives compaction. The OpenSpec apply flow uses it. See
the plan_exec section of the `openspec-apply-change` skill.

## Why

A long apply run keeps progress in conversation memory, and memory does
not survive compaction. The ledger is the record that does. The brief
keeps each task's exact values out of a dispatch prompt that would
otherwise carry the whole plan. The package hands a reviewer one file
instead of a diff pasted into the reviewer's context.

## Commands

The gate tools come from the shared repository venv. The unit is
`zai-routing-audit-python-deps` in `tools/project_setup/registry.json`.
Its interpreter runs every gate in this repository, including this one.

```bash
VENV=tools/zai_routing_audit/.venv/bin/python
```

Extract a task brief (accepts `N` and dotted `X.Y`; reads section plans
and OpenSpec checkbox plans; fenced blocks protect their content):

```bash
$VENV -m plan_exec brief --plan openspec/changes/<id>/tasks.md --task 2.3 --out .plan_exec/<id>
```

Package a commit range for review (read-only against the repo; `--head`
defaults to `HEAD`):

```bash
$VENV -m plan_exec package --repo . --base <sha> --out .plan_exec/<id>
```

Keep the execution ledger (append-only; single writer by design):

```bash
$VENV -m plan_exec ledger --plan <plan.md> --dir .plan_exec/<id> init
$VENV -m plan_exec ledger --plan <plan.md> --dir .plan_exec/<id> complete --task 1.2 --tests "pytest -k t" --result "3 passed"
$VENV -m plan_exec ledger --plan <plan.md> --dir .plan_exec/<id> task-rule --task 2.1 --what "..." --why "..." --cost "..."
$VENV -m plan_exec ledger --plan <plan.md> --dir .plan_exec/<id> show
```

Put the global `--json` flag before the subcommand for machine-readable
output:

```bash
$VENV -m plan_exec --json ledger --plan <plan.md> --dir .plan_exec/<id> show
```

Exit code 0 means success. Exit code 2 means an operational failure, for
example an unknown task, a missing plan, a non-repository target, base
equal to head, a foreign ledger identity, an unknown git revision, a
missing action flag, or an output path that cannot be written. The
command writes only under the given `--out` directory (or the default
ledger directory below) and never deletes.

## The ledger

`ledger init` writes `<dir>/progress.md` with the identity line
`# plan_exec ledger - plan: <absolute plan path>`. Without `--dir`, the
ledger sits at `<repo-root>/.plan_exec/<plan file name>/progress.md`,
which is git-ignored: the ledger is per-run scratch. The durable record
of a change stays in its `tasks.md` ticks and in git history. Run
`show` after a compaction. Trust the ledger and `git log` over
recollection. When the default directory already holds another plan's
ledger, pass `--dir .plan_exec/<change-id>`. One agent works one plan,
so concurrent appends are out of scope. Appends verify the identity
value, so an append through a wrong directory refuses.

## Tests and gates

```bash
VENV=tools/zai_routing_audit/.venv/bin/python
$VENV -m pytest tests/plan_exec -q
$VENV -m pytest tests/plan_exec --cov plan_exec --cov-branch --cov-fail-under=100 --cov-config .coveragerc
$VENV -m ruff check tools/plan_exec
```

Ruff reads `tools/plan_exec/ruff.toml` (C901 with a maximum complexity
of 10). Coverage runs with the root `.coveragerc`.

### Mutation run

Run mutmut on an out-of-tree copy, never inside the repository:

```bash
rm -rf /tmp/pe_mut && mkdir -p /tmp/pe_mut/pe/tests
rsync -a --exclude .venv --exclude __pycache__ --exclude .ruff_cache \
  tools/plan_exec/ /tmp/pe_mut/pe/
cp -r tests/plan_exec/. /tmp/pe_mut/pe/tests/
cd /tmp/pe_mut/pe
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut run
/full/path/to/lab/tools/zai_routing_audit/.venv/bin/python -m mutmut results
```

The unmutated copy passes first (`PYTHONPATH=/tmp/pe_mut/pe $VENV -m
pytest tests/`). Each survivor is a missing assertion: add a test until
it dies, or exclude it with a written reason. Target: 95 percent or
higher. `__main__.py` carries a `do_not_mutate_patterns` exclusion: the
two-line shim holds no logic, the same reason the coverage omit lists
it.

### Equivalent-mutant classes (written reasons)

The final run settles at 36 survivors of 725 mutants, a score of 95.0
percent. Every survivor sits in a measured equivalence class. No tool
config is loosened; every mutant keeps its name here.

- Encoding kwargs set to `None` or `"UTF-8"`, or removed (17 mutants:
  `x_write_package__mutmut_68,70,89`, `x__read_ledger__mutmut_4,6`,
  `x_init__mutmut_21,23,28`, `x__append__mutmut_13,15,17,21`,
  `x_write_brief__mutmut_2,4,27,29,31`): the repository and the CI image
  pin UTF-8 locales. `None` resolves to UTF-8 under them, and `"UTF-8"`
  names the same codec.
- `subprocess.run(check=False)` set to `None` or removed (4 mutants:
  `package.x__git__mutmut_5,9`, `ledger.x__repo_root__mutmut_5,9`):
  `check=None` equals `check=False`.
- The command `"git"` spelled `"GIT"` (2 mutants:
  `package.x__git__mutmut_11`, `ledger.x__repo_root__mutmut_11`): the
  macOS development filesystem is case-insensitive and resolves it. A
  case-sensitive CI filesystem kills it.
- `rstrip()` replaced with `lstrip()` on git output (3 mutants:
  `x_write_package__mutmut_79,83,87`): `git log` and `git diff` output
  carries no leading or trailing whitespace.
- `_repo_root`'s `and` swapped to `or` (1 mutant:
  `ledger.x__repo_root__mutmut_19`): the branches differ only when git
  fails with non-empty standard output, which real git does not produce.
- The ledger directory and file names re-cased (2 mutants:
  `ledger.x_ledger_path__mutmut_13,15`): same case-insensitive macOS
  filesystem as above.
- The `--dir` default `None` removed (1 mutant:
  `cli.x__build_parser__mutmut_142`): argparse's own default is `None`.
- `allow_abbrev=False` set to `None` (4 mutants:
  `cli.x__build_parser__mutmut_3,36,73,118`): `None` is falsy like
  `False`, so the abbreviation rejection behaves identically.
- The fence-state initializer `False` set to `None` (2 mutants:
  `brief.x__section_body__mutmut_2`, `brief.x__checkbox_body__mutmut_2`):
  both values are falsy, and `_in_fence` normalizes the state on the
  next fence marker.

## Status

Windows support for the SessionStart hook this tool accompanies is
out of scope for now (repo development is macOS; CI is ubuntu). TBD if
the harness ever adds a Windows surface.
