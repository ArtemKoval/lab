"""Behavior tests for the status subcommand in process_issues."""

import json
import os
from datetime import datetime, timezone

from process_issues import cli, core, lock, status

NOW = 1_700_000_000.0


def make_rec(**over):
    """Return one canonical lock record with overrides."""
    rec = {
        "version": 1,
        "holder": "loop-20261107-a",
        "host": "h1",
        "boot_id": "b1",
        "pid": 4242,
        "pid_start": "123",
        "acquired_at": datetime.fromtimestamp(NOW, tz=timezone.utc).isoformat(),
    }
    rec.update(over)
    return rec


def write_lock(root, rec):
    """Write one record as the lock file under the state dir."""
    path = root / "lock.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec), encoding="utf-8")
    return path


def fresh_rec(holder="loop-live", pid=None, pid_start=None):
    """Return a record that looks fresh on this host and boot."""
    if pid is None:
        pid = os.getpid()
    if pid_start is None:
        pid_start = lock.start_time(pid)
    return make_rec(holder=holder, host=lock.this_host(),
                    boot_id=lock.this_boot_id(), pid=pid,
                    pid_start=pid_start,
                    acquired_at=datetime.now(timezone.utc).isoformat())


def dead_pid():
    """Return one pid that no longer runs."""
    proc = subprocess_wait_true()
    return proc.pid


def subprocess_wait_true():
    """Start one true process and wait for it."""
    import subprocess
    proc = subprocess.Popen(["true"])
    proc.wait()
    return proc


class FakeGh:
    """Stub runner over canned gh results."""

    def __init__(self, calls):
        self.calls = calls
        self.index = 0

    def __call__(self, args):
        if self.index >= len(self.calls):
            return 1, "", "no more stubbed calls"
        code, out, err = self.calls[self.index]
        self.index += 1
        return code, out, err


ISSUES = json.dumps([
    {"number": 9, "title": "plain work", "labels": []},
    {"number": 12, "title": "stuck work", "labels": [{"name": "blocked"}]},
    {"number": 15, "title": "handover doc", "labels": [{"name": "handover"},
                                                       {"name": "blocked"}]},
])

ISSUES_CLEAN = json.dumps([
    {"number": 9, "title": "plain work", "labels": []},
    {"number": 15, "title": "handover doc", "labels": [{"name": "handover"}]},
])


def test_decide_rows_in_order():
    assert status.decide(halt="stop") == (status.LEVEL_HALT, 1, "stop")
    assert status.decide(halt="stop", auth_error="setup") == \
        (status.LEVEL_HALT, 1, "stop")
    assert status.decide(auth_error="setup") == (status.LEVEL_AUTH, 3,
                                                 "setup")
    assert status.decide(auth_error="setup", list_error="boom") == \
        (status.LEVEL_AUTH, 3, "setup")
    assert status.decide(list_error="boom") == (status.LEVEL_ISSUE_LIST, 2,
                                                "boom")
    assert status.decide(blocked=[(9, "t")])[0] == status.LEVEL_BLOCKED
    assert status.decide(blocked=[(9, "t")], lock_row=(status.LEVEL_RUNNING,
                                                       0, "")) == \
        (status.LEVEL_BLOCKED, 2, "blocked issues need the operator: #9")
    row = (status.LEVEL_RUNNING, 0, "")
    assert status.decide(lock_row=row) == row
    assert status.decide() == (status.LEVEL_IDLE, 1,
                               "idle: no lock file stands")


def test_halt_reason_strips_and_falls_back():
    assert status.halt_reason("  operator pause  \n") == "operator pause"
    assert status.halt_reason("") == status.HALT_FALLBACK
    assert status.halt_reason(None) == status.HALT_FALLBACK


def test_blocked_reason_names_numbers():
    assert status.blocked_reason([(12, "stuck"), (20, "more")]) == \
        "blocked issues need the operator: #12, #20"


def test_lock_row_mappings():
    assert status.lock_row(error="cannot read") == (status.LEVEL_LOCK, 2,
                                                    "cannot read")
    assert status.lock_row(verdict_kind="fresh") == \
        (status.LEVEL_RUNNING, 0, "")
    assert status.lock_row(verdict_kind="own") == \
        (status.LEVEL_RUNNING, 0, "")
    assert status.lock_row(verdict_kind="stale", rule="pid") == \
        (status.LEVEL_STALE, 1, "stale lock: pid")
    assert status.lock_row(verdict_kind="free") == \
        (status.LEVEL_IDLE, 1, "idle: no lock file stands")


def test_lock_summary_states():
    assert status.lock_summary(None, None, None) is None
    assert status.lock_summary("fresh", "loop-x", None) == \
        {"state": "held", "holder": "loop-x", "rule": None}
    assert status.lock_summary("stale", "loop-x", "pid")["state"] == "stale"
    assert status.lock_summary("free", None, None)["state"] == "absent"
    assert status.lock_summary("unreadable", None, None)["state"] == \
        "unreadable"


def no_git(args):
    """Runner that refuses the git call."""
    return 1, "", "tests use no real git"


def run_status(tmp_path, calls, argv=("status",), capsys=None):
    """Run the status CLI rooted at tmp_path with a fake runner."""
    fake = FakeGh(calls)
    code = cli.main(list(argv), runner=fake, repo_root=str(tmp_path),
                    git_runner=no_git)
    captured = capsys.readouterr()
    return code, captured, fake


def test_cli_halt_row_makes_no_gh_call(tmp_path, capsys):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "halt").write_text("operator pause\nmore\n")
    code, captured, fake = run_status(tmp_path, [], capsys=capsys)
    assert code == 1
    assert "operator pause" in captured.err
    assert captured.out == ""
    assert fake.index == 0


def test_cli_halt_working_root_wins(tmp_path, capsys):
    main_root = tmp_path / "main"
    main_root.mkdir()
    (main_root / ".claude").mkdir()
    (main_root / ".claude" / "halt").write_text("primary stop\n")
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "halt").write_text("working stop\n")
    fake = FakeGh([])
    primary_git = lambda args: (0, str(main_root / ".git") + "\n", "")
    code = cli.main(["status"], runner=fake, repo_root=str(tmp_path),
                    git_runner=primary_git)
    captured = capsys.readouterr()
    assert code == 1
    assert "working stop" in captured.err
    assert "primary stop" not in captured.err
    assert fake.index == 0


def test_cli_empty_halt_file_reports_fallback(tmp_path, capsys):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "halt").write_text("\n \n")
    code, captured, fake = run_status(tmp_path, [], capsys=capsys)
    assert code == 1
    assert "the halt file stands" in captured.err
    assert fake.index == 0


def test_cli_halt_primary_root(tmp_path, capsys):
    main_root = tmp_path / "main"
    main_root.mkdir()
    (main_root / ".claude").mkdir()
    (main_root / ".claude" / "halt").write_text("primary stop\n")
    fake = FakeGh([])
    primary_git = lambda args: (0, str(main_root / ".git") + "\n", "")
    code = cli.main(["status"], runner=fake, repo_root=str(tmp_path / "repo"),
                    git_runner=primary_git)
    captured = capsys.readouterr()
    assert code == 1
    assert "primary stop" in captured.err
    assert fake.index == 0


def test_cli_missing_token_reports_setup(tmp_path, capsys):
    code, captured, fake = run_status(tmp_path, [(1, "", "not logged in")],
                                      capsys=capsys)
    assert code == 3
    assert "setup" in captured.err
    assert "not logged in" not in captured.err
    assert fake.index == 1


def test_cli_empty_token_reports_setup(tmp_path, capsys):
    code, captured, _ = run_status(tmp_path, [(0, "   \n", "")],
                                   capsys=capsys)
    assert code == 3
    assert captured.err.count("\n") == 1


def test_cli_failed_list_reports_component_error(tmp_path, capsys):
    code, captured, fake = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (1, "", "api down")],
        capsys=capsys)
    assert code == 2
    assert "api down" in captured.err
    assert captured.err.count("\n") == 1
    assert fake.index == 2


def test_cli_blocked_issue_reports_and_names(tmp_path, capsys):
    code, captured, _ = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES, "")], capsys=capsys)
    assert code == 2
    assert "#12" in captured.err
    code, captured, _ = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES, "")],
        argv=("status", "--json"), capsys=capsys)
    payload = json.loads(captured.out)
    assert payload["level"] == "blocked" and payload["code"] == 2
    assert payload["blocked"] == [{"number": 12, "title": "stuck work"}]
    assert payload["lock"] is None


def test_cli_handover_outranks_blocked(tmp_path, capsys):
    only_handover = json.dumps([
        {"number": 15, "title": "handover doc",
         "labels": [{"name": "handover"}, {"name": "blocked"}]},
    ])
    code, captured, fake = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, only_handover, "")],
        capsys=capsys)
    assert code == 1
    assert fake.index == 2


def test_cli_fresh_lock_reports_running(tmp_path, capsys):
    state = tmp_path / ".process_issues"
    write_lock(state, fresh_rec(holder="loop-live"))
    code, captured, fake = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES_CLEAN, "")], capsys=capsys)
    assert code == 0
    assert captured.err == "" and captured.out == ""
    assert fake.index == 2
    code, captured, _ = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES_CLEAN, "")],
        argv=("status", "--json"), capsys=capsys)
    payload = json.loads(captured.out)
    assert payload == {
        "level": "running", "code": 0, "reason": "",
        "blocked": None,
        "lock": {"state": "held", "holder": "loop-live", "rule": None},
    }


def test_cli_stale_lock_reports_restartable(tmp_path, capsys):
    write_lock(tmp_path / ".process_issues", fresh_rec(pid=dead_pid(),
                                                       pid_start="7"))
    code, captured, _ = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES_CLEAN, "")], capsys=capsys)
    assert code == 1
    assert "stale" in captured.err


def test_cli_idle_reports_restartable(tmp_path, capsys):
    code, captured, fake = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES_CLEAN, "")], capsys=capsys)
    assert code == 1
    assert "idle" in captured.err
    code, captured, _ = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES_CLEAN, "")],
        argv=("status", "--json"), capsys=capsys)
    payload = json.loads(captured.out)
    assert payload["level"] == "idle"
    assert payload["lock"]["state"] == "absent"


def test_cli_unreadable_lock_reports_component_error(tmp_path, capsys):
    path = write_lock(tmp_path / ".process_issues", fresh_rec())
    path.chmod(0o000)
    try:
        code, captured, _ = run_status(
            tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES_CLEAN, "")],
            capsys=capsys)
        code_json, captured_json, _ = run_status(
            tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES_CLEAN, "")],
            argv=("status", "--json"), capsys=capsys)
    finally:
        path.chmod(0o600)
    assert code == 2
    assert "cannot read" in captured.err
    assert captured.err.count("process_issues: process_issues:") == 0
    payload = json.loads(captured_json.out)
    assert payload["level"] == "lock" and payload["code"] == 2
    assert payload["lock"]["state"] == "unreadable"


def test_cli_corrupt_lock_is_stale(tmp_path, capsys):
    write_lock(tmp_path / ".process_issues", {})
    code, captured, _ = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES_CLEAN, "")], capsys=capsys)
    assert code == 1
    assert "stale" in captured.err


def test_cli_unparsable_lock_is_stale(tmp_path, capsys):
    write_lock(tmp_path / ".process_issues", "not json {")
    code, captured, _ = run_status(
        tmp_path, [(0, "tokentoken\n", ""), (0, ISSUES_CLEAN, "")], capsys=capsys)
    assert code == 1
    assert "stale" in captured.err


def test_state_for_labels_walks_the_precedence():
    assert core.state_for_labels({"handover", "blocked"}) == "skip"
    assert core.state_for_labels({"blocked"}) == "blocked"
    assert core.state_for_labels({"answered"}) == "answered"
    assert core.state_for_labels({"human-approved"}) is None
    assert core.state_for_labels(set()) is None


def test_run_git_real_call_reports_nonzero_text_output(tmp_path):
    code, out, err = cli.run_git(
        ["git", "-C", str(tmp_path), "rev-parse", "--git-common-dir"])
    assert code != 0
    assert isinstance(out, str) and isinstance(err, str)
    assert out == ""
