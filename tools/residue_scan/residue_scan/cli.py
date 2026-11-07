"""Scan local branches and worktrees into the residue report.

Exit 0 when no residue sits in the repository, 2 when the scan finds
residue or cannot gather its facts, and 0 after a successful prune.
`--prune` deletes the reported branches and their registered worktrees;
without it the scan is read-only.
"""

import argparse
import json
import subprocess
import sys

from . import core

BRANCH_FIELDS = "number,headRefName"


def _run_tool(program, args):
    """Run one external call and return (code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            [program, *args], capture_output=True, text=True, check=False
        )
    except OSError as exc:
        return 1, "", f"the {program} call failed: {exc}"
    return proc.returncode, proc.stdout, proc.stderr


def run_git(args):
    """Run one git call and return (code, stdout, stderr)."""
    return _run_tool("git", args)


def run_gh(args):
    """Run one gh call and return (code, stdout, stderr)."""
    return _run_tool("gh", args)


def runner(argv):
    """Dispatch one call by its program name."""
    if argv[0] == "gh":
        return run_gh(argv[1:])
    return run_git(argv[1:])


def fetch(runner, argv):
    """Return (data, error). The data is None when the call or parse fails."""
    code, out, err = runner(argv)
    if code != 0:
        return None, err.strip() or f"the call exited with code {code}"
    try:
        return json.loads(out), None
    except json.JSONDecodeError as exc:
        return None, f"the output is not valid JSON: {exc}"


def list_branches(runner):
    """Return the local branch names, or (None, error)."""
    fmt = "--format=%(refname:short)"
    code, out, err = runner(["git", "for-each-ref", "refs/heads", fmt])
    if code != 0:
        return None, err.strip() or "the branch list failed"
    return [line.strip() for line in out.splitlines() if line.strip()], None


def count_ahead(runner, base, branch):
    """Return the commit count from base to one branch, or None."""
    code, out, _ = runner(["git", "rev-list", "--count", f"{base}..{branch}"])
    if code != 0:
        return None
    try:
        return int(out.strip())
    except ValueError:
        return None


def list_worktrees(runner):
    """Return ((path, branch) pairs, error) from the porcelain worktree list."""
    code, out, err = runner(["git", "worktree", "list", "--porcelain"])
    if code != 0:
        return None, err.strip() or "the worktree list failed"
    pairs = []
    path = ""
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch "):
            ref = line[len("branch "):]
            pairs.append((path, ref.removeprefix("refs/heads/")))
    return pairs, None


def pr_map(runner, state):
    """Return the branch-to-PR-number map for one PR state, or (None, error).

    The call pages through the full list, so a truncation can never hide
    an open pull request behind the page size and hand a live branch to
    the prune.
    """
    data, error = fetch(
        runner,
        ["gh", "pr", "list", "--state", state, "--paginate", "--json", BRANCH_FIELDS],
    )
    if data is None:
        return None, error
    mapping = {}
    for item in data:
        branch = item.get("headRefName")
        if branch:
            mapping[branch] = item.get("number")
    return mapping, None


def gather(runner, base):
    """Return (branches, worktrees, merged, opened, error)."""
    names, error = list_branches(runner)
    if names is None:
        return None, None, None, None, error
    branches = []
    for name in names:
        if not core.is_typed(name):
            continue
        ahead = count_ahead(runner, base, name)
        if ahead is None:
            return None, None, None, None, f"the commit count failed for {name}"
        branches.append((name, ahead))
    merged, error = pr_map(runner, "merged")
    if merged is None:
        return None, None, None, None, f"the merged pull request list failed: {error}"
    opened, error = pr_map(runner, "open")
    if opened is None:
        return None, None, None, None, f"the open pull request list failed: {error}"
    worktrees, error = list_worktrees(runner)
    if worktrees is None:
        return None, None, None, None, f"the worktree list failed: {error}"
    return branches, worktrees, merged, opened, None


def prune(entries, runner):
    """Delete the residue entries. Return the refusal notes.

    The worktrees go first: a branch that a registered worktree still
    has checked out refuses deletion.
    """
    notes = []
    for entry in entries:
        if entry["kind"] != "worktree":
            continue
        code, _, err = runner(["git", "worktree", "remove", entry["name"]])
        if code != 0:
            notes.append(f"the worktree {entry['name']} refused removal: {err.strip()}")
    for entry in entries:
        if entry["kind"] != "branch":
            continue
        code, _, err = runner(["git", "branch", "-D", entry["name"]])
        if code != 0:
            notes.append(f"the branch {entry['name']} refused deletion: {err.strip()}")
    return notes


def _emit(entries, as_json):
    """Print the report and return the findings exit code."""
    if as_json:
        print(json.dumps(entries))
        return 2 if entries else 0
    if not entries:
        print("No residue.")
        return 0
    for entry in entries:
        source = f" (PR #{entry['pr']})" if entry["pr"] else ""
        print(f"{entry['kind']}\t{entry['name']}\t{entry['reason']}{source}")
    return 2


def main(argv=None, run=None, repo_root=None):
    """Run the scan or prune subcommand and return the exit code."""
    parser = argparse.ArgumentParser(prog="residue_scan")
    parser.add_argument("command", choices=["scan", "prune"])
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--base", default="main", help="The mainline ref")
    parser.add_argument(
        "--repo-root", default=None, help="The repository root for git calls"
    )
    args = parser.parse_args(argv)
    root_arg = repo_root if repo_root is not None else args.repo_root

    def dispatch(call_argv):
        program = call_argv[0]
        if root_arg is not None and program == "git":
            call_argv = ["git", "-C", root_arg, *call_argv[1:]]
        return run(call_argv) if run is not None else runner(call_argv)

    branches, worktrees, merged, opened, error = gather(dispatch, args.base)
    if error:
        print(f"residue_scan: {error}", file=sys.stderr)
        return 2
    entries = core.collect_residue(branches, worktrees, merged, opened)
    code = _emit(entries, args.as_json)
    if args.command == "prune":
        notes = prune(entries, dispatch)
        for note in notes:
            print(note, file=sys.stderr)
        return 2 if notes else 0
    return code
