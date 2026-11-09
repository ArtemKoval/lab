#!/usr/bin/env python3
"""The dead-code scanner for the owned tools.

The scanner runs vulture over Python files and reports unused code.
It reads the tree and never edits. The scan is opt-in: no pipeline
step runs it, and a later change promotes it to a gate on evidence
from the first runs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 2
DEFAULT_CONFIDENCE = 60
SKIP_DIRS = {
    "tests",
    "venv",
    ".venv",
    "dist",
    "build",
    "node_modules",
    "__pycache__",
    ".git",
}


def python_files(root):
    """Yield the Python files under root, skipping vendored trees."""
    if root.is_file():
        if root.suffix == ".py":
            yield root
        return
    for path in sorted(root.rglob("*.py")):
        if not any(part in SKIP_DIRS for part in path.parts):
            yield path


def scan(paths, min_confidence):
    """Return (findings, errors) for the paths at the confidence.

    Each finding carries the file, the line, the name, and the type.
    A missing vulture is an operational error with the install
    command in the message.
    """
    try:
        from vulture import Vulture
    except ImportError as exc:
        install = "pip install -r tools/dead_export_scan/requirements.txt"
        return [], [f"vulture missing: {exc}; install it with {install}"]
    findings = []
    errors = []
    files = []
    for path in paths:
        root = Path(path)
        if not root.exists():
            errors.append(f"path missing: {path}")
            continue
        files.extend(str(item) for item in python_files(root))
    if files:
        vulture = Vulture()
        vulture.scavenge(files)
        for item in vulture.get_unused_code(min_confidence=min_confidence):
            findings.append(
                {
                    "file": str(item.filename),
                    "line": item.first_lineno,
                    "name": item.name,
                    "type": item.typ,
                }
            )
    return findings, errors


def print_text(report):
    """Print the report as one line per finding plus the errors."""
    for finding in report["findings"]:
        print(
            f"{finding['file']}:{finding['line']}: "
            f"{finding['name']} ({finding['type']})"
        )
    for line in report["errors"]:
        print(f"error: {line}")


def parse_args(argv):
    """Return the parsed CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["tools"],
        help="directories to scan (default: tools)",
    )
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=DEFAULT_CONFIDENCE,
        help="vulture confidence threshold (default: 60)",
    )
    parser.add_argument("--json", action="store_true", help="json output")
    return parser.parse_args(argv)


def main(argv=None):
    """Run the scan and return the exit code."""
    args = parse_args(argv)
    findings, errors = scan(args.paths, args.min_confidence)
    report = {"ok": not errors and not findings, "findings": findings, "errors": errors}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return EXIT_OK if report["ok"] else EXIT_FAIL


if __name__ == "__main__":
    sys.exit(main())
