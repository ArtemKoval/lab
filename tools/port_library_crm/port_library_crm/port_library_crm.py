"""Port the library_crm child repository into this one through a
three-way merge.

The script fetches the child head, computes `git merge-tree --write-tree`
against the fork base, applies the merged tree to the current branch,
restores the excluded paths, and writes the merge report. Excluded paths
(`openspec/specs/`) stay owned by the change deltas, which the archive flow
applies later. A nonempty deletion set is an operational failure: this port
expects additions and modifications only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

EXCLUDED_PREFIXES = ("openspec/specs/",)
CHILD_REF_DEFAULT = "210247d"
BASE_DEFAULT = "05c3ddd"
REPORT_DIR_DEFAULT = "reports/port_library_crm"

_DIFF_SEP = "\t"


class GitError(Exception):
    """A git command returned a nonzero code."""

    def __init__(self, args: list[str], code: int, out: str):
        self.args = list(args)
        self.code = code
        self.out = out
        super().__init__(f"git {' '.join(args)} failed with {code}: {out.strip()}")


class OperationalFailure(Exception):
    """An operational failure that carries one next action."""

    def __init__(self, message: str, remediation: str):
        self.message = message
        self.remediation = remediation
        super().__init__(f"{message} Next: {remediation}")


def run_git(args: list[str], cwd: Path | None = None) -> str:
    """Run one git command in cwd and return its stdout."""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise GitError(args, proc.returncode, proc.stdout + proc.stderr)
    return proc.stdout


def parse_merge_tree_output(text: str) -> tuple[str, list[str]]:
    """Split the merge-tree output into the tree oid and the conflict list."""
    lines = text.splitlines()
    tree = lines[0].strip() if lines else ""
    conflicted: list[str] = []
    for line in lines[1:]:
        parts = line.split(_DIFF_SEP, 1)
        if len(parts) != 2:
            continue
        meta = parts[0].split()
        if len(meta) == 3 and meta[2] in ("1", "2", "3"):
            path = parts[1]
            if path not in conflicted:
                conflicted.append(path)
    return tree, conflicted


def classify_changed_files(
    name_status_text: str, excluded_prefixes: tuple[str, ...] = ()
) -> dict[str, list]:
    """Bucket the `git diff --name-status` output by change kind."""
    buckets: dict[str, list] = {
        "copied": [],
        "transferred": [],
        "renamed": [],
        "deletions": [],
        "excluded": [],
        "excluded_status": [],
    }
    for line in name_status_text.splitlines():
        if not line.strip():
            continue
        parts = line.split(_DIFF_SEP)
        status = parts[0][0]
        if status == "R":
            buckets["renamed"].append((parts[1], parts[2]))
            continue
        path = parts[1]
        if any(path.startswith(prefix) for prefix in excluded_prefixes):
            buckets["excluded"].append(path)
            buckets["excluded_status"].append((path, status))
        elif status == "A":
            buckets["copied"].append(path)
        elif status == "M":
            buckets["transferred"].append(path)
        elif status == "D":
            buckets["deletions"].append(path)
    return buckets


def build_report(
    copied: list[str],
    transferred: list[str],
    deletions: list[str],
    conflicted: list[str],
    excluded: list[str],
    base: str,
    child_head: str,
) -> dict:
    """Assemble the merge report with the deletions row."""
    return {
        "base": base,
        "child_head": child_head,
        "copied": sorted(copied),
        "transferred": sorted(transferred),
        "deletions": sorted(deletions),
        "conflicted": sorted(conflicted),
        "excluded": sorted(excluded),
        "total": len(copied) + len(transferred) + len(deletions) + len(excluded),
    }


def render_markdown(report: dict) -> str:
    """Render the report as a short markdown document."""
    lines = [
        "# port-library-crm merge report",
        "",
        f"- base: {report['base']}",
        f"- child head: {report['child_head']}",
        f"- copied: {len(report['copied'])}",
        f"- transferred: {len(report['transferred'])}",
        f"- deletions: {len(report['deletions'])}",
        f"- conflicted: {len(report['conflicted'])}",
        f"- excluded: {len(report['excluded'])}",
        f"- total: {report['total']}",
        "",
    ]
    for kind in ("deletions", "conflicted", "excluded"):
        if report[kind]:
            lines.append(f"## {kind}")
            lines.append("")
            for path in report[kind]:
                lines.append(f"- {path}")
            lines.append("")
    return "\n".join(lines)


def _restore_excluded(
    runner, excluded_status: list[tuple[str, str]], repo_root: Path
) -> None:
    """Put every excluded path back to its HEAD state.

    A path that HEAD carries returns through checkout. A path that only the
    merged tree adds leaves through rm.
    """
    for path, status in sorted(excluded_status):
        if status == "M":
            runner(["checkout", "HEAD", "--", path], cwd=repo_root)
        else:
            runner(["rm", "-f", "--quiet", path], cwd=repo_root)


def apply_port(
    runner,
    repo_root: Path,
    child_source: str,
    child_ref: str,
    base: str,
    report_dir: Path,
) -> dict:
    """Run the whole port flow and return the report."""
    try:
        runner(["fetch", child_source, child_ref], cwd=repo_root)
        child_head = runner(["rev-parse", "FETCH_HEAD"], cwd=repo_root).strip()
    except GitError as exc:
        raise OperationalFailure(
            f"the fetch of {child_source} {child_ref} failed",
            "check the child source path and the credentials, then rerun "
            "the fetch",
        ) from exc
    merge_args = [
        "merge-tree",
        "--write-tree",
        f"--merge-base={base}",
        "HEAD",
        child_head,
    ]
    try:
        merge_text = runner(merge_args, cwd=repo_root)
    except GitError as exc:
        # merge-tree exits 1 when the merge conflicts; the merged tree still
        # lands on stdout's first line.
        if exc.code != 1:
            raise
        merge_text = exc.out
    tree, conflicted = parse_merge_tree_output(merge_text)
    diff_text = runner(
        ["diff", "--name-status", "--no-renames", "HEAD", tree],
        cwd=repo_root,
    )
    buckets = classify_changed_files(diff_text, EXCLUDED_PREFIXES)
    if buckets["deletions"]:
        names = ", ".join(buckets["deletions"])
        raise OperationalFailure(
            f"the merge carries {len(buckets['deletions'])} deletion(s): {names}",
            "examine the deletion set against the child history, record it "
            "in the change artifacts, and extend the script before applying",
        )
    runner(["checkout", tree, "--", "."], cwd=repo_root)
    _restore_excluded(runner, buckets["excluded_status"], repo_root)
    applied_conflicts = [p for p in conflicted if p not in buckets["excluded"]]
    report = build_report(
        copied=buckets["copied"],
        transferred=buckets["transferred"],
        deletions=buckets["deletions"],
        conflicted=applied_conflicts,
        excluded=buckets["excluded"],
        base=base,
        child_head=child_head,
    )
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (report_dir / "report.md").write_text(render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    """Run the CLI: apply the port and print the counts."""
    parser = argparse.ArgumentParser(
        prog="port_library_crm",
        description="Port the library_crm child repository through a "
        "three-way merge.",
    )
    parser.add_argument("--json", action="store_true", help="machine output")
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument(
        "--child-source",
        required=True,
        help="the child repository path or URL to fetch",
    )
    parser.add_argument("--child-ref", default=CHILD_REF_DEFAULT)
    parser.add_argument("--base", default=BASE_DEFAULT)
    parser.add_argument("--report-dir", default=REPORT_DIR_DEFAULT)
    args = parser.parse_args(argv)
    repo_root = Path(args.repo_root)
    report_dir = Path(args.report_dir)
    try:
        report = apply_port(
            runner=run_git,
            repo_root=repo_root,
            child_source=args.child_source,
            child_ref=args.child_ref,
            base=args.base,
            report_dir=report_dir,
        )
    except OperationalFailure as exc:
        if args.json:
            print(json.dumps({"ok": False, "remediation": exc.remediation}))
        else:
            print(f"FAIL: {exc.message}. Next: {exc.remediation}", file=sys.stderr)
        return 2
    if args.json:
        payload = dict(report)
        payload["ok"] = True
        print(json.dumps(payload))
    else:
        print(f"copied: {len(report['copied'])}")
        print(f"transferred: {len(report['transferred'])}")
        print(f"conflicted: {len(report['conflicted'])}")
        print(f"excluded: {len(report['excluded'])}")
        print(f"report: {report_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
