#!/usr/bin/env python3
"""The setup doctor for the project-setup registry.

Read-only by default: the doctor validates the registry file and
reports the plan. Each unit of the plan carries its status and its
exact install command. `--units` runs the named units' check commands
and classifies them as present or absent. `--install` refuses a
blanket run: it requires `--units`, runs the install command of each
absent named unit, and re-runs the check as the readback. A readback
mismatch is a failure.

Exit 0 means a valid registry and verified installs. Exit 2 names an
invalid registry, an unknown unit, a failed install, or a readback
mismatch.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REQUIRED_FIELDS = ("id", "kind", "check", "install")
EXIT_OK = 0
EXIT_FAIL = 2
REGISTRY_RELATIVE = Path("tools") / "project_setup" / "registry.json"


def load_registry(path):
    """Return (units, defects) for the registry file at path."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [], [f"registry unreadable: {exc}"]
    if not isinstance(data, dict) or not isinstance(data.get("units"), list):
        return [], ["registry holds no units list"]
    defects = []
    seen = set()
    for unit in data["units"]:
        defects.extend(_unit_defects(unit, seen))
    return data["units"], defects


def _unit_defects(unit, seen):
    """Return the defects of one registry unit."""
    if not isinstance(unit, dict):
        return ["unit is not an object"]
    unit_id = unit.get("id")
    if not unit_id:
        return ["unit misses id"]
    defects = []
    if unit_id in seen:
        defects.append(f"unit id repeats: {unit_id}")
    seen.add(unit_id)
    for field in REQUIRED_FIELDS:
        if field not in unit:
            defects.append(f"unit {unit_id} misses {field}")
    return defects


def plan_units(units, requested):
    """Return (rows, errors) for the requested unit ids.

    A row carries the unit and the status. The status starts as
    `unchecked` and becomes `present` or `absent` after a check run.
    """
    known = {}
    for unit in units:
        if isinstance(unit, dict) and unit.get("id"):
            known[unit["id"]] = unit
    errors = []
    for unit_id in requested or ():
        if unit_id not in known:
            errors.append(f"unknown unit: {unit_id}")
    rows = [
        {"id": unit_id, "unit": unit, "status": "unchecked"}
        for unit_id, unit in known.items()
        if not requested or unit_id in requested
    ]
    return rows, errors


def run_check(command, cwd):
    """Return the exit code of one check command run in cwd."""
    try:
        done = subprocess.run(command, cwd=str(cwd), check=False)
    except OSError as exc:
        print(f"check command failed to start: {exc}", file=sys.stderr)
        return 127
    return done.returncode


def examine(rows, cwd):
    """Run each row's check and set the status to present or absent."""
    for row in rows:
        code = run_check(row["unit"]["check"], cwd)
        row["status"] = "present" if code == 0 else "absent"
    return rows


def run_install_command(install, cwd):
    """Return the exit code of one install command run in cwd."""
    if isinstance(install, list):
        done = subprocess.run(install, cwd=str(cwd), check=False)
        return done.returncode
    done = subprocess.run(install, cwd=str(cwd), shell=True, check=False)
    return done.returncode


def install_rows(rows, cwd):
    """Install absent rows and read back. Return the failure lines."""
    failures = []
    for row in rows:
        if row["status"] == "present":
            continue
        code = run_install_command(row["unit"]["install"], cwd)
        if code != 0:
            row["status"] = "install_failed"
            failures.append(f"install failed: {row['id']}")
            continue
        readback = run_check(row["unit"]["check"], cwd)
        if readback != 0:
            row["status"] = "readback_mismatch"
            failures.append(f"readback mismatch: {row['id']}")
        else:
            row["status"] = "installed"
    return failures


def plan_view(rows):
    """Return the public view of the rows for text and json output."""
    view = []
    for row in rows:
        install = row["unit"]["install"]
        if isinstance(install, list):
            install = " ".join(install)
        view.append({"id": row["id"], "status": row["status"], "install": install})
    return view


def print_text(report):
    """Print the report as one line per unit plus the error lines."""
    for unit in report["units"]:
        print(f"{unit['id']}: {unit['status']}")
        print(f"  install: {unit['install']}")
    for line in report["errors"]:
        print(f"error: {line}")


def parse_args(argv):
    """Return the parsed CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--json", action="store_true", help="json output")
    parser.add_argument(
        "--units", default="", help="comma-separated unit ids to examine"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="install the absent units named by --units",
    )
    return parser.parse_args(argv)


def run_flow(args, repo_root):
    """Return (rows, errors, failures) for the parsed arguments."""
    units, defects = load_registry(repo_root / REGISTRY_RELATIVE)
    requested = [part for part in args.units.split(",") if part]
    rows, errors = [], list(defects)
    if not errors:
        rows, errors = plan_units(units, requested)
    failures = []
    if not errors:
        if requested:
            examine(rows, repo_root)
            if args.install:
                failures = install_rows(rows, repo_root)
        elif args.install:
            errors.append("--install requires --units")
    return rows, errors, failures


def main(argv=None):
    """Run the doctor and return the exit code."""
    args = parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    rows, errors, failures = run_flow(args, repo_root)
    report = {
        "ok": not errors and not failures,
        "units": plan_view(rows),
        "errors": errors + failures,
    }
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return EXIT_OK if report["ok"] else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
