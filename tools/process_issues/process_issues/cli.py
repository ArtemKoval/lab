"""Scan open issues into the process-issues queue.

The scan exits 0 on success, 2 on an operational failure, and 64 on a
usage error. The status command exits 0 running, 1 stopped or
restartable, 2 on a component error, and 3 waiting for setup.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import authors
from . import core
from . import ledger
from . import lock
from . import status

DEFAULT_LIMIT = "200"
ISSUE_FIELDS = "number,title,createdAt,labels,author"
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


def author_login(issue):
    """Return the author login from the fetch payload, or None."""
    author = issue.get("author")
    if not isinstance(author, dict):
        return None
    login = author.get("login")
    return login if isinstance(login, str) else None


def build_queue(issues, prs, repo_root, allowed):
    """Assemble the sorted, classified queue for the open issues.

    The admission gate runs before the label classification, and a
    refused issue carries the refused state with no further assessment.
    """
    dirs = active_change_dirs(repo_root)
    normalize_pr_states(prs)
    queue = []
    for issue in core.sorted_issues(issues):
        login = author_login(issue)
        labels = {label.get("name") for label in issue.get("labels", [])}
        entry = {
            "number": issue.get("number"),
            "title": issue.get("title"),
            "createdAt": issue.get("createdAt"),
            "author": login,
            "labels": sorted(label for label in labels if label),
            "prs": [],
            "changeDir": None,
        }
        if not core.admitted(login, allowed):
            entry["state"] = core.STATE_REFUSED
            entry["action"] = core.ACTION_NONE
            queue.append(entry)
            continue
        raw_linked = core.linked_prs(prs, issue.get("number"))
        linked = linked_prs(raw_linked)
        change_dir = core.linked_change_dir(raw_linked, dirs)
        verdict = core.classify(
            labels, raw_linked, change_dir is not None, title=issue.get("title") or ""
        )
        entry["state"] = verdict["state"]
        entry["action"] = verdict["action"]
        entry["prs"] = linked
        entry["changeDir"] = change_dir
        queue.append(entry)
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
            text = halt.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not text.strip():
            return status.HALT_FALLBACK
        return status.halt_reason(text.splitlines()[0])
    return None


def _auth_error(runner):
    """Return the setup reason when the local gh token probe fails."""
    code, out, _err = runner(["auth", "token"])
    if code != 0 or not out.strip():
        return status.AUTH_REASON
    return None


def _blocked_entries(issues, allowed):
    """Return the blocked entries through the scan label precedence.

    The admission gate runs before the blocked test, so a refused
    foreign issue never pages the operator.
    """
    entries = []
    for issue in core.sorted_issues(issues):
        login = author_login(issue)
        if not core.admitted(login, allowed):
            continue
        labels = {label.get("name") for label in issue.get("labels", [])}
        if core.state_for_labels(labels) == core.STATE_BLOCKED:
            entries.append((issue.get("number"), issue.get("title")))
    return entries


def _lock_facts(state_dir):
    """Return (kind, rule, holder, read_reason) for the lock rows.

    The read reason loses the process_issues prefix, because the status
    output adds its own prefix once at the print boundary.
    """
    exists, record, error = lock.read_record(lock.lock_path(state_dir))
    if error is not None:
        prefix = "process_issues: "
        reason = error[len(prefix):] if error.startswith(prefix) else error
        return "unreadable", None, None, reason
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
        return {"halt": halt, "auth_error": None, "config_error": None,
                "list_error": None, "blocked": None, "lock_row": None,
                "lock_summary": None}
    facts = {"halt": None, "auth_error": None, "config_error": None,
             "list_error": None, "blocked": None, "lock_row": None,
             "lock_summary": None}
    facts["auth_error"] = _auth_error(runner)
    if facts["auth_error"] is not None:
        return facts
    try:
        allowed = authors.load_authors()
    except authors.AuthorsError as exc:
        facts["config_error"] = str(exc)
        return facts
    issues, list_error = _fetch(
        runner,
        ["issue", "list", "--state", "open", "--limit", DEFAULT_LIMIT,
         "--json", "number,title,labels,author"],
    )
    facts["list_error"] = list_error
    if list_error is not None:
        return facts
    entries = _blocked_entries(issues, allowed)
    if entries:
        facts["blocked"] = entries
        return facts
    kind, rule, holder, read_error = _lock_facts(state_dir)
    facts["lock_row"] = status.lock_row(error=read_error,
                                        verdict_kind=kind, rule=rule)
    facts["lock_summary"] = status.lock_summary(kind, holder, rule)
    return facts


def _run_status(args, runner, repo_root, state_dir):
    """Run the status subcommand. Return the exit code."""
    facts = _gather_status(runner, repo_root, state_dir)
    level, code, reason = status.decide(
        halt=facts["halt"], auth_error=facts["auth_error"],
        config_error=facts["config_error"],
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
    try:
        allowed = authors.load_authors()
    except authors.AuthorsError as exc:
        print(f"process_issues: {exc}", file=sys.stderr)
        return 2
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
    queue = build_queue(issues, prs, repo_root, allowed)
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


def _ledger_usage(args):
    """Return the usage exit code for the ledger arguments, or None."""
    if args.action is None:
        print("process_issues: ledger needs an action", file=sys.stderr)
        return 64
    if args.action == "write" and (not args.kind or not args.key):
        print("process_issues: ledger write needs --kind and --key",
              file=sys.stderr)
        return 64
    if args.action == "write" and args.kind not in ledger.KINDS:
        print("process_issues: ledger write needs a known --kind",
              file=sys.stderr)
        return 64
    if args.action == "confirm" and not args.marker_id:
        print("process_issues: ledger confirm needs --id", file=sys.stderr)
        return 64
    return None


def _run_ledger(args, state_dir):
    """Run the ledger command. Return the exit code."""
    usage = _ledger_usage(args)
    if usage is not None:
        return usage
    path = ledger.ledger_path(state_dir)
    try:
        if args.action == "write":
            return _ledger_write(path, args.kind, str(args.key))
        if args.action == "confirm":
            return _ledger_confirm(path, args.marker_id)
        return _ledger_pending(path, args.as_json)
    except ledger.LedgerError as exc:
        print(f"process_issues: {exc}", file=sys.stderr)
        return 2


def _ledger_write(path, kind, key):
    """Run the write action. Return the exit code."""
    records, _notes = ledger.read_records(path)
    ids = {row.get("id") for row in records}
    marker = ledger.new_marker(ids)
    live_groups = {
        (row.get("kind"), row.get("key"))
        for row in ledger.pending_view(records)
    }
    payload = {
        "event": ledger.EVENT_INTENT,
        "id": marker,
        "kind": kind,
        "key": key,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    ledger.append_record(path, payload)
    if (kind, key) in live_groups:
        print(
            f"process_issues: the group {kind} {key} already carries a "
            f"live pending intent",
            file=sys.stderr,
        )
    print(marker)
    return 0


def _ledger_confirm(path, marker):
    """Run the confirm action. Return the exit code."""
    records, _notes = ledger.read_records(path)
    known = {}
    for row in records:
        if row.get("id") == marker:
            known[marker] = row.get("event") == ledger.EVENT_INTENT
    if marker not in known:
        print(f"process_issues: unknown ledger marker {marker}",
              file=sys.stderr)
        return 2
    if not known[marker]:
        return 0
    ledger.append_record(path, {
        "event": ledger.EVENT_CONFIRMED,
        "id": marker,
        "at": datetime.now(timezone.utc).isoformat(),
    })
    return 0


def _ledger_pending(path, as_json):
    """Run the pending action. Return the exit code."""
    records, notes = ledger.read_records(path)
    for note in notes:
        print(f"process_issues: {note}", file=sys.stderr)
    rows = ledger.pending_view(records)
    if as_json:
        print(json.dumps(rows))
        return 0
    for row in rows:
        superseded = "superseded" if row["superseded"] else "live"
        print(f"{row['id']}\t{row['kind']}\t{row['key']}\t{row['at']}"
              f"\t{superseded}")
    return 0


def main(argv=None, runner=run_gh, repo_root=None, git_runner=run_git):
    """Run one CLI command and return the exit code."""
    parser = argparse.ArgumentParser(prog="process_issues")
    parser.add_argument("command", choices=["scan", "acquire", "release",
                                            "status", "ledger"])
    parser.add_argument("action", nargs="?", choices=["write", "confirm",
                                                      "pending"],
                        default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--holder", dest="holder")
    parser.add_argument("--force", action="store_true", dest="force")
    parser.add_argument("--kind", dest="kind")
    parser.add_argument("--key", dest="key")
    parser.add_argument("--id", dest="marker_id")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 0 if exc.code in (0, None) else 64
    if repo_root is None:
        repo_root = Path.cwd()
    state_dir = lock.resolve_state_dir(repo_root, git_runner)
    if args.command != "ledger" and args.action is not None:
        print(f"process_issues: {args.command} takes no action argument",
              file=sys.stderr)
        return 64
    if args.command == "scan":
        return _run_scan(args, runner, repo_root, state_dir)
    if args.command == "status":
        return _run_status(args, runner, repo_root, state_dir)
    if args.command == "ledger":
        return _run_ledger(args, state_dir)
    return _run_lock(args, state_dir)
