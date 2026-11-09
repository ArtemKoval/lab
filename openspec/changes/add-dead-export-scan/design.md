# Design: add-dead-export-scan

## Plan review

The review kept the report proposal as the plan. ASIT: Multiplication,
with the justification that no existing gate sees a trivial dead
export. The sec-scan tool is the existing pattern for a scanner in the
house style, and the new scan is a second instance of that pattern,
parameterized by the dead-code detector.

Alternatives the review rejected:

- A ruff-based rule. Ruff's F401 sees unused imports in one file, and
  the unused-export problem crosses files. Vulture cross-references a
  whole tree.
- A gate on day one. The report scopes the scan as an opt-in report,
  and a gate without evidence buries the run under unknown false
  positives.
- A whitelist file on day one. No false positive names itself yet, and
  vulture's confidence filter is the first filter.

## The CLI contract

`dead_export_scan.py` follows the house contract: read-only scan,
`--json` with an `ok` field, exit 0 on a clean scan and 2 on findings
or an operational failure. The flags:

- `--paths` takes one or more directories and defaults to the owned
  tool directories under `tools/`.
- `--min-confidence` takes vulture's confidence threshold and defaults
  to 60, which names unused code without style noise.
- `--json` prints one object with `ok`, the findings, and the errors.

The tool imports vulture lazily, so `--help` works on a clone without
the dependency, and the registry `check` command runs a scoped clean
scan. The scan walks `*.py` files under the given paths, skips
`tests`, `venv`, `dist`, `build`, `node_modules`, and `__pycache__`,
and reports each finding with its file, line, name, and type.

## The tests

`tests/dead_export_scan/test_dead_export_scan.py` builds fixture
trees. A tree with a dead function, an unused class, and an unused
import names all three. A clean tree exits 0 with an empty findings
list. The `--json` output carries the shape. A missing dependency
reports an operational failure through a patched import. The tests run
vulture in process through the scan function, so the coverage run sees
the module, and one CLI smoke run exercises `--help` as a subprocess.

## The gate-list wiring

The workflow whitelist and the coverage `--source` list gain
`dead_export_scan`, and the two pin tests in
`tests/claude_infra/test_ci_workflow.py` gain the same directory, so
the pins match the file. The operator acknowledged these protected
paths, and the merge of the implementation pull request carries the
acceptance.

## Edge cases

- A scoped scan over a directory with no Python files exits 0 with an
  empty findings list, because an empty scope is a clean scan.
- A vulture import failure is an operational failure: exit 2, an
  error line, and the install command in the message.
- The scan reports but never edits. No flag mutates the tree.
