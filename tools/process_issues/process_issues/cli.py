"""Scan open issues into the process-issues queue.

Exit 0 on success, 2 on operational failure, and 64 on a usage error.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from . import core
from . import lock
from . import status

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


def run_git(args):
    """Run one git call and return (code, stdout, stderr)."""
    try:
        proc = subprocess.run(
            args, capture_output=True, text=True, check=False
        )
    except OSError as exc:
        return 1, "", f"the git call failed: {exc}"
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


def _print_note(note):
    """Print one stderr note when one exists."""
    if note:
        print(note, file=sys.stderr)


def _lock_inputs():
    """Assemble the real liveness inputs for the lock module."""
    return {
        "probe": lock.probe_live,
        "host": lock.this_host(),
        "boot_id": lock.this_boot_id(),
        "now": time.time(),
        "caller_pid": lock.session_anchor()[0],
    }


def _halt_reason(repo_root, state_dir):
    """Return the halt reason from the working root or the primary root.

    The working root wins when both files stand, in the manner of the
    hook precedence. None marks no halt file in either location.
    """
    primary_root = Path(state_dir).parent
    for root in (Path(repo_root), primary_root):
        halt = root / ".claude" / "halt"
        try:
            first = halt.read_text(encoding="utf-8").splitlines()[0]
        except (OSError, IndexError):
            continue
        return status.halt_reason(first)
    return None


def _auth_error(runner):
    """Return the setup reason when the local gh token probe fails."""
    code, out, _err = runner(["auth", "token"])
    if code != 0 or not out.strip():
        return status.AUTH_REASON
    return None


def _blocked_entries(issues):
    """Return the blocked entries through the scan label precedence."""
    entries = []
    for issue in core.sorted_issues(issues):
        labels = {label.get("name") for label in issue.get("labels", [])}
        if core.state_for_labels(labels) == core.STATE_BLOCKED:
            entries.append((issue.get("number"), issue.get("title")))
    return entries


def _lock_facts(state_dir):
    """Return (kind, rule, holder, read_error) for the lock rows."""
    exists, record, error = lock.read_record(lock.lock_path(state_dir))
    if error is not None:
        return "unreadable", None, None, error
    kind, rule = lock.verdict(
        exists, record, holder=None, probe=lock.probe_live,
        host=lock.this_host(), boot_id=lock.this_boot_id(), now=time.time()
    )
    holder = record.get("holder") if record else None
    return kind, rule, holder, None


def _gather_status(runner, repo_root, state_dir):
    """Gather the status facts in row order and stop at the first match."""
    halt = _halt_reason(repo_root, state_dir)
    if halt is not None:
        return {"halt": status.halt_reason(halt), "auth_error": None,
                "list_error": None, "blocked": None, "lock_row": None,
                "lock_summary": None}
    facts = {"halt": None, "auth_error": None, "list_error": None,
             "blocked": None, "lock_row": None, "lock_summary": None}
    facts["auth_error"] = _auth_error(runner)
    if facts["auth_error"] is not None:
        return facts
    issues, list_error = _fetch(
        runner,
        ["issue", "list", "--state", "open", "--limit", DEFAULT_LIMIT,
         "--json", "number,title,labels"],
    )
    facts["list_error"] = list_error
    if list_error is not None:
        return facts
    entries = _blocked_entries(issues)
    if entries:
        facts["blocked"] = entries
        return facts
    kind, rule, holder, read_error = _lock_facts(state_dir)
    facts["lock_row"] = status.lock_row(error=read_error,
                                        verdict_kind=kind, rule=rule)
    facts["lock_summary"] = status.lock_summary(
        None if read_error else kind, holder, rule
    )
    return facts


def _run_status(args, runner, repo_root, state_dir):
    """Run the status subcommand. Return the exit code."""
    facts = _gather_status(runner, repo_root, state_dir)
    level, code, reason = status.decide(
        halt=facts["halt"], auth_error=facts["auth_error"],
        list_error=facts["list_error"], blocked=facts["blocked"],
        lock_row=facts["lock_row"]
    )
    if args.as_json:
        payload = {
            "level": level,
            "code": code,
            "reason": reason,
            "blocked": None,
            "lock": facts["lock_summary"],
        }
        if level == status.LEVEL_BLOCKED:
            payload["blocked"] = [
                {"number": number, "title": title}
                for number, title in facts["blocked"]
            ]
        print(json.dumps(payload))
    elif code != 0:
        print(f"process_issues: {reason}", file=sys.stderr)
    return code


def _run_lock(args, state_dir):
    """Run the acquire or release command. Return the exit code."""
    if args.command == "acquire" and not args.holder:
        print("process_issues: acquire needs --holder LABEL", file=sys.stderr)
        return 64
    if args.command == "acquire" and args.force:
        print("process_issues: acquire takes no --force", file=sys.stderr)
        return 64
    if args.command == "release" and not args.holder and not args.force:
        print("process_issues: release needs --holder LABEL or --force",
              file=sys.stderr)
        return 64
    if args.command == "acquire":
        code, note = lock.acquire(state_dir, args.holder, **_lock_inputs())
    else:
        code, note = lock.release(state_dir, holder=args.holder, force=args.force)
    _print_note(note)
    return code


def _run_scan(args, runner, repo_root, state_dir):
    """Run the scan subcommand. Return the exit code."""
    code, note = lock.examine(state_dir, holder=args.holder, **_lock_inputs())
    _print_note(note)
    if code != 0:
        return code
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


def main(argv=None, runner=run_gh, repo_root=None, git_runner=run_git):
    """Run one CLI command and return the exit code."""
    parser = argparse.ArgumentParser(prog="process_issues")
    parser.add_argument("command", choices=["scan", "acquire", "release",
                                            "status"])
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--holder", dest="holder")
    parser.add_argument("--force", action="store_true", dest="force")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else 64
    if repo_root is None:
        repo_root = Path.cwd()
    state_dir = lock.resolve_state_dir(repo_root, git_runner)
    if args.command == "scan":
        return _run_scan(args, runner, repo_root, state_dir)
    if args.command == "status":
        return _run_status(args, runner, repo_root, state_dir)
    return _run_lock(args, state_dir)
