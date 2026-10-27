"""The spec_ste_check command line.

With explicit paths it scans those files and trees. With no paths it
scans the gate scope: `openspec/specs/**` plus the active directories
under `openspec/changes/**`, always skipping `openspec/changes/archive/`.
Exit 0 means a clean scan, 2 means at least one error or an operational
failure.
"""

import argparse
import json
import sys
from pathlib import Path

from . import rules


def _files_under(directory):
    return sorted(directory.rglob("*.md"))


def collect_files(args):
    """Resolve the scan set: explicit paths, or the default gate scope."""
    if args.paths:
        files = []
        for raw in args.paths:
            path = Path(raw)
            if path.is_dir():
                files.extend(_files_under(path))
            else:
                files.append(path)
        return files
    base = Path(args.repo_root) / "openspec"
    files = []
    specs = base / "specs"
    if specs.is_dir():
        files.extend(_files_under(specs))
    changes = base / "changes"
    if changes.is_dir():
        files.extend(
            path
            for path in _files_under(changes)
            if path.relative_to(changes).parts[0] != "archive"
        )
    return files


def scan(path):
    """Check one file and return its violations."""
    text = path.read_text(encoding="utf-8")
    return rules.check_text(text, str(path))


def _print_human(violations, count):
    for violation in violations:
        print(
            f"{violation['file']}:{violation['line']}: {violation['severity']}"
            f": {violation['rule']}: {violation['text']}"
        )
    errors = sum(1 for v in violations if v["severity"] == "error")
    print(
        f"{errors} errors, {len(violations) - errors} warnings "
        f"in {count} files",
        file=sys.stderr,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="spec_ste_check",
        description="Report mechanical ASD-STE100 violations in spec text.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="files or trees to scan; default: the gate scope",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="print a JSON report on stdout",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="repository root for the default gate scope",
    )
    args = parser.parse_args(argv)

    violations = []
    files = collect_files(args)
    for path in files:
        try:
            violations.extend(scan(path))
        except OSError as error:
            print(f"spec_ste_check: cannot read {path}: {error}", file=sys.stderr)
            return 2

    if args.as_json:
        errors = [v for v in violations if v["severity"] == "error"]
        print(
            json.dumps(
                {
                    "violations": violations,
                    "errors": len(errors),
                    "warnings": len(violations) - len(errors),
                }
            )
        )
    else:
        _print_human(violations, len(files))
    return 2 if any(v["severity"] == "error" for v in violations) else 0
