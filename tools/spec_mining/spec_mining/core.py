"""Pure scans and report builders for the spec mining audit.

The module holds no I/O. The CLI gathers the facts (the tree walk, the
archive parse, the git log) and hands them here in plain data shapes.
"""

import fnmatch


def normalize(name):
    """Return one lowercase kebab token for a unit name.

    The rule strips one trailing extension, turns each underscore into a
    dash, and collapses repeated dashes.
    """
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return "-".join(part for part in name.lower().replace("_", "-").split("-") if part)


def _patterns(value):
    """Return the capability globs for one data-file value."""
    if isinstance(value, str):
        return [value]
    return list(value)


def _name_covered(unit, aliases, specs):
    """Return True when the name rule or the alias covers one unit."""
    base = unit.rsplit("/", 1)[-1]
    if normalize(base) in specs:
        return True
    return aliases.get(unit) in specs


def _entry_covered(unit, entries, specs):
    """Return True when every capability glob of one entry matches."""
    patterns = _patterns(entries[unit])
    return all(
        any(fnmatch.fnmatchcase(spec, pattern) for spec in specs)
        for pattern in patterns
    )


def scan_tree(units, specs, data):
    """Return the uncovered units and the stale data-file entries.

    units maps one class name to its unit paths. specs is the set of
    capability names in openspec/specs/. data is the parsed units.json.
    Every class follows the name rule first; the data file entries cover
    the rest. An alias counts only when its capability exists.
    """
    specs = set(specs)
    aliases = data.get("aliases", {})
    coverage = data.get("coverage", {})
    projects = data.get("projects", {})
    uncovered = []
    for klass in ("tools", "hooks", "skills", "projects"):
        entries = coverage if klass == "skills" else projects
        for unit in units.get(klass, []):
            if _name_covered(unit, aliases, specs):
                continue
            if unit in entries and _entry_covered(unit, entries, specs):
                continue
            uncovered.append({"unit": unit, "class": klass})
    seen = {row["unit"] for row in units_list(units)}
    stale = sorted(
        key
        for source in (aliases, coverage, projects)
        for key in source
        if key not in seen
    )
    return {"uncovered": uncovered, "stale": stale}


def units_list(units):
    """Return every walked unit path as one flat list of rows."""
    return [
        {"unit": unit, "class": klass}
        for klass in ("tools", "hooks", "skills", "projects")
        for unit in units.get(klass, [])
    ]


def scan_drift(archive, specs):
    """Return the archived scenarios the capability specs lost.

    archive rows carry the change name, the capability, and the scenario
    names of the ADDED and MODIFIED delta sections. A capability with no
    spec directory marks every one of its archived scenarios.
    """
    drift = []
    for row in archive:
        held = set(specs.get(row["capability"], ()))
        missing = row["capability"] not in specs
        for scenario in row["scenarios"]:
            if scenario in held:
                continue
            drift.append(
                {
                    "change": row["change"],
                    "capability": row["capability"],
                    "scenario": scenario,
                    "missing_spec": missing,
                }
            )
    return drift


def rank(counts):
    """Order the uncovered areas by commit count, then by name."""
    rows = [{"area": area, "commits": count} for area, count in counts.items()]
    rows.sort(key=lambda row: (-row["commits"], row["area"]))
    return rows
