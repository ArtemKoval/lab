"""Structure and reference pin for the committed units.json data file.

The pin walks the real repository, so a data-file entry whose unit left
the tree or whose capability glob matches nothing fails here.
"""

import json
import fnmatch
from pathlib import Path

from spec_mining import cli

REPO_ROOT = Path(__file__).absolute().parents[2]

DATA = json.loads(
    (REPO_ROOT / "tools" / "spec_mining" / "spec_mining" / "units.json").read_text()
)
UNITS = cli._walk(REPO_ROOT)
SPECS = set(cli._spec_scenarios(REPO_ROOT))
ALL_UNITS = {row["unit"] for row in cli.core.units_list(UNITS)}


def test_the_data_file_holds_exactly_the_three_maps():
    assert set(DATA) == {"aliases", "projects", "coverage"}


def test_every_value_holds_the_documented_shape():
    for unit, capability in DATA["aliases"].items():
        assert isinstance(capability, str), unit
    for unit, globs in DATA["projects"].items():
        assert isinstance(globs, list) and globs, unit
    for unit, value in DATA["coverage"].items():
        assert isinstance(value, (str, list)), unit


def test_every_referenced_unit_exists_in_the_tree():
    for source in ("aliases", "coverage", "projects"):
        for unit in DATA[source]:
            assert unit in ALL_UNITS, f"stale {source} entry: {unit}"


def test_every_capability_reference_resolves():
    referenced = list(DATA["aliases"].values())
    for globs in DATA["projects"].values():
        referenced.extend(globs)
    for value in DATA["coverage"].values():
        referenced.extend(value if isinstance(value, list) else [value])
    for pattern in referenced:
        assert any(
            fnmatch.fnmatchcase(spec, pattern) for spec in SPECS
        ), f"unresolved capability pattern: {pattern}"


def test_the_alias_example_is_grounded():
    assert DATA["aliases"]["tools/spec_ste_check"] == "spec-ste-enforcement"
    assert "spec-ste-enforcement" in SPECS
