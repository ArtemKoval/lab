"""Scan open issues into the process-issues queue.

Exit 0 on success and 2 on operational failure.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import core

DEFAULT_LIMIT = "200"
ISSUE_FIELDS = "number,title,createdAt,labels"
PR_FIELDS = "number,state,headRefName,body"


def run_gh(args):
    """Run one gh call and return (code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            ["gh", *args], capture_output=True, text=True, check=False
        )
    except OSError as exc:
        return 1, "", f"the gh call failed: {exc}"
    return proc.returncode, proc.stdout, proc.stderr


def _fetch(runner, args):
    """Return (data, error). The data is None when the call or parse fails."""
    code, out, err = runner(args)
    if code != 0:
        return None, err.strip() or f"gh exited with code {code}"
    try:
        return json.loads(out), None
    except json.JSONDecodeError as exc:
        return None, f"the gh output is not valid JSON: {exc}"


def linked_prs(raw_linked):
    """Map the raw linked PRs to the queue's output shape."""
    return [
        {
            "number": pr.get("number"),
            "state": pr.get("state"),
            "branch": pr.get("headRefName") or "",
        }
        for pr in raw_linked
    ]


def normalize_pr_states(prs):
    """Lowercase the state of every PR, because gh emits upper case."""
    for pr in prs:
        if isinstance(pr, dict) and pr.get("state"):
            pr["state"] = pr["state"].lower()


def active_change_dirs(repo_root):
    """List the active change dir names under openspec/changes."""
    base = Path(repo_root) / "openspec" / "changes"
    if not base.is_dir():
        return []
    return sorted(
        path.name
        for path in base.iterdir()
        if path.is_dir() and path.name != "archive" and not path.name.startswith(".")
    )


def build_queue(issues, prs, repo_root):
    """Assemble the sorted, classified queue for the open issues."""
    dirs = active_change_dirs(repo_root)
    normalize_pr_states(prs)
    queue = []
    for issue in core.sorted_issues(issues):
        labels = {label.get("name") for label in issue.get("labels", [])}
        raw_linked = core.linked_prs(prs, issue.get("number"))
        linked = linked_prs(raw_linked)
        change_dir = core.linked_change_dir(raw_linked, dirs)
        verdict = core.classify(labels, raw_linked, change_dir is not None)
        queue.append(
            {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "createdAt": issue.get("createdAt"),
                "labels": sorted(label for label in labels if label),
                "state": verdict["state"],
                "action": verdict["action"],
                "prs": linked,
                "changeDir": change_dir,
            }
        )
    return queue


def main(argv=None, runner=run_gh, repo_root=None):
    """Run the scan subcommand and return the exit code."""
    parser = argparse.ArgumentParser(prog="process_issues")
    parser.add_argument("command", choices=["scan"])
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    if repo_root is None:
        repo_root = Path.cwd()
    issues, error = _fetch(
        runner,
        [
            "issue", "list", "--state", "open",
            "--limit", DEFAULT_LIMIT, "--json", ISSUE_FIELDS,
        ],
    )
    if issues is None:
        print(f"process_issues: the issue list failed: {error}", file=sys.stderr)
        return 2
    prs, error = _fetch(
        runner,
        ["pr", "list", "--state", "all", "--limit", DEFAULT_LIMIT, "--json", PR_FIELDS],
    )
    if prs is None:
        print(f"process_issues: the pr list failed: {error}", file=sys.stderr)
        return 2
    queue = build_queue(issues, prs, repo_root)
    if args.as_json:
        print(json.dumps(queue))
    else:
        for item in queue:
            links = "; ".join(
                f"#{pr['number']} {pr['state']}" for pr in item["prs"]
            )
            print(
                f"{item['number']}\t{item['state']}\t{item['action']}"
                f"\t{links}\t{item['title']}"
            )
    return 0
