"""Behavior tests for the loop lock in process_issues.lock."""

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone

from process_issues import cli, lock

NOW = 1_700_000_000.0
YOUNG = datetime.fromtimestamp(NOW, tz=timezone.utc).isoformat()
OLD = (datetime.fromtimestamp(NOW, tz=timezone.utc) - timedelta(hours=25)).isoformat()
EDGE = (datetime.fromtimestamp(NOW, tz=timezone.utc) - timedelta(hours=24)).isoformat()

RECORD_KEYS = {
    "version", "holder", "host", "boot_id", "pid", "pid_start", "acquired_at",
}


def make_rec(**over):
    """Return one canonical record with overrides."""
    rec = {
        "version": 1,
        "holder": "loop-20261107-a",
        "host": "h1",
        "boot_id": "b1",
        "pid": 4242,
        "pid_start": "123",
        "acquired_at": YOUNG,
    }
    rec.update(over)
    return rec


def probe_ok(pid, start):
    """Probe that always says the process runs."""
    return None


def probe_dead(pid, start):
    """Probe that says the process is gone."""
    return "pid"


def probe_start(pid, start):
    """Probe that says the start time differs."""
    return "start"


def write_lock(root, rec):
    """Write one record as the lock file under the state dir."""
    path = root / "lock.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rec), encoding="utf-8")
    return path


def write_raw(root, text):
    """Write raw bytes as the lock file under the state dir."""
    path = root / "lock.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def judge(rec, *, holder=None, caller_pid=None, probe=probe_ok, host="h1",
          boot="b1", now=NOW, exists=True):
    """Run one verdict with canonical inputs."""
    return lock.verdict(exists, rec, holder=holder, probe=probe, host=host,
                        boot_id=boot, now=now, caller_pid=caller_pid)


def rule_of(rec, *, probe=probe_ok, host="h1", boot="b1", now=NOW):
    """Run one stale judgment with canonical inputs."""
    return lock.stale_rule(rec, probe=probe, host=host, boot_id=boot, now=now)


def take(root, holder="loop-b", *, probe=probe_ok, caller_pid=None, pid=5, **over):
    """Run one acquire with canonical inputs."""
    return lock.acquire(
        root, holder, probe=probe, host="h1", boot_id="b1", now=NOW,
        pid=pid, pid_start="7", caller_pid=caller_pid, **over
    )


def test_free_when_no_file(tmp_path):
    exists, rec, error = lock.read_record(tmp_path / "lock.json")
    assert (exists, rec, error) == (False, None, None)
    assert judge(None, exists=False)[0] == "free"


def test_read_record_shapes(tmp_path):
    write_raw(tmp_path, "not json {")
    assert lock.read_record(tmp_path / "lock.json") == (True, None, None)
    write_raw(tmp_path, "[1, 2]")
    assert lock.read_record(tmp_path / "lock.json") == (True, None, None)
    path = write_lock(tmp_path, make_rec())
    exists, rec, error = lock.read_record(path)
    assert (exists, error) == (True, None)
    assert rec["holder"] == "loop-20261107-a"


def test_read_record_unreadable_names_the_path(tmp_path):
    path = write_lock(tmp_path, make_rec())
    path.chmod(0o000)
    try:
        exists, rec, error = lock.read_record(path)
    finally:
        path.chmod(0o600)
    assert exists is True and rec is None
    assert "lock.json" in error and "cannot read" in error


def test_stale_rule_matches_corrupt_first():
    assert rule_of(None) == "corrupt"


def test_stale_rule_matches_unknown_version():
    assert rule_of(make_rec(version=2)) == "version"
    assert rule_of({"holder": "x"}) == "version"


def test_stale_rule_matches_age():
    assert rule_of(make_rec(acquired_at=OLD)) == "age"
    assert rule_of(make_rec(acquired_at="nonsense")) == "age"
    assert rule_of(make_rec(acquired_at=None)) == "age"


def test_stale_rule_age_boundary_stays_fresh():
    assert rule_of(make_rec(acquired_at=EDGE)) is None


def test_stale_rule_foreign_host_stays_fresh_when_young():
    assert rule_of(make_rec(host="elsewhere")) is None


def test_stale_rule_foreign_host_ages_out():
    assert rule_of(make_rec(host="elsewhere", acquired_at=OLD)) == "age"


def test_stale_rule_matches_boot():
    assert rule_of(make_rec(boot_id="other-boot")) == "boot"


def test_stale_rule_anchorless_record_stays_fresh():
    assert rule_of(make_rec(pid=None, pid_start=None)) is None


def test_stale_rule_matches_pid_and_start():
    assert rule_of(make_rec(), probe=probe_dead) == "pid"
    assert rule_of(make_rec(), probe=probe_start) == "start"
    assert rule_of(make_rec(), probe=probe_ok) is None


def test_verdict_paths():
    assert judge(make_rec(), exists=False)[0] == "free"
    kind, rule = judge(make_rec(), probe=probe_dead)
    assert (kind, rule) == ("stale", "pid")
    assert judge(make_rec(), holder="loop-20261107-a")[0] == "own"
    assert judge(make_rec(pid=999), caller_pid=999)[0] == "own"
    assert judge(make_rec(pid=999), caller_pid=1000)[0] == "fresh"
    assert judge(make_rec(), holder="loop-20261107-a", probe=probe_dead)[0] == "stale"


def test_make_record_shape():
    rec = lock.make_record("loop-x", pid=10, pid_start="55", host="h9",
                           boot_id="b9", now=NOW)
    assert set(rec) == RECORD_KEYS
    assert rec["version"] == 1
    assert rec["holder"] == "loop-x"
    assert rec["pid_start"] == "55"
    assert rec["host"] == "h9" and rec["boot_id"] == "b9"
    assert lock._parse_time(rec["acquired_at"]) == NOW


def test_acquire_reuses_the_state_dir(tmp_path):
    (tmp_path / "lock.json").parent.mkdir(parents=True, exist_ok=True)
    code, note = take(tmp_path, "loop-b")
    assert code == 0
    assert holder_of(tmp_path) == "loop-b"


def test_acquire_creates_missing_state_dirs(tmp_path):
    code, note = take(tmp_path / "sub" / "state", "loop-b")
    assert code == 0
    assert holder_of(tmp_path / "sub" / "state") == "loop-b"


def test_acquire_free_writes_canonical_record(tmp_path):
    code, note = take(tmp_path, "loop-b")
    assert (code, note) == (0, "")
    rec = json.loads((tmp_path / "lock.json").read_text())
    assert set(rec) == RECORD_KEYS
    assert rec["holder"] == "loop-b"
    assert rec["pid"] == 5 and rec["pid_start"] == "7"
    assert rec["host"] == "h1" and rec["boot_id"] == "b1"
    assert rec["version"] == 1


def test_acquire_own_label_is_idempotent(tmp_path):
    take(tmp_path, "loop-b")
    before = (tmp_path / "lock.json").read_text()
    code, note = take(tmp_path, "loop-b")
    assert (code, note) == (0, "")
    assert (tmp_path / "lock.json").read_text() == before


def test_acquire_own_caller_pid_is_idempotent(tmp_path):
    write_lock(tmp_path, make_rec(pid=777))
    code, note = take(tmp_path, "loop-other", caller_pid=777)
    assert (code, note) == (0, "")


def test_acquire_fresh_foreign_refuses_and_keeps_the_file(tmp_path):
    path = write_lock(tmp_path, make_rec(pid=4242))
    code, note = take(tmp_path, "loop-b")
    assert code == 2
    assert note == (
        "process_issues: the lock is held by 'loop-20261107-a' on 'h1' "
        "(pid 4242); release --force clears it"
    )
    assert json.loads(path.read_text())["holder"] == "loop-20261107-a"


def test_acquire_clears_stale_and_takes(tmp_path):
    write_lock(tmp_path, make_rec(pid=4242))
    code, note = take(tmp_path, "loop-b", probe=probe_dead)
    assert code == 0
    assert note == (
        "process_issues: cleared a stale lock (pid) and took it for loop-b"
    )
    rec = json.loads((tmp_path / "lock.json").read_text())
    assert rec["holder"] == "loop-b"


def test_acquire_clears_corrupt_and_takes(tmp_path):
    write_raw(tmp_path, "{oops")
    code, note = take(tmp_path, "loop-b")
    assert code == 0 and "corrupt" in note


def test_acquire_clears_unknown_version_and_takes(tmp_path):
    write_lock(tmp_path, make_rec(version=99))
    code, note = take(tmp_path, "loop-b")
    assert code == 0 and "version" in note


def test_acquire_clears_old_age_and_takes(tmp_path):
    write_lock(tmp_path, make_rec(acquired_at=OLD))
    code, note = take(tmp_path, "loop-b")
    assert code == 0 and "age" in note


def test_acquire_clears_boot_mismatch_and_takes(tmp_path):
    write_lock(tmp_path, make_rec(boot_id="previous-boot"))
    code, note = take(tmp_path, "loop-b")
    assert code == 0 and "boot" in note


def test_acquire_clears_start_mismatch_and_takes(tmp_path):
    write_lock(tmp_path, make_rec())
    code, note = take(tmp_path, "loop-b", probe=probe_start)
    assert code == 0 and "start" in note


def test_acquire_unreadable_record_refuses(tmp_path):
    path = write_lock(tmp_path, make_rec())
    path.chmod(0o000)
    try:
        code, note = take(tmp_path, "loop-b")
    finally:
        path.chmod(0o600)
    assert code == 2 and "cannot read" in note


def test_acquire_race_refuses_with_holder_details(tmp_path):
    path = write_lock(tmp_path, make_rec(holder="loop-racer", pid=4242))
    code, note = lock._create(tmp_path, path, "loop-b", probe=probe_ok,
                              host="h1", boot_id="b1", now=NOW, pid=5,
                              pid_start="7", note="")
    assert code == 2
    assert "loop-racer" in note


def test_acquire_state_dir_failure_refuses(tmp_path):
    state = tmp_path / ".process_issues"
    state.symlink_to(tmp_path / "nowhere")
    code, note = take(state, "loop-b")
    assert code == 2
    assert "cannot create the state dir" in note


def test_release_force_clears_an_unreadable_file(tmp_path):
    path = write_lock(tmp_path, make_rec())
    path.chmod(0o000)
    try:
        code, note = lock.release(tmp_path, holder="loop-20261107-a", force=True)
    finally:
        if path.exists():
            path.chmod(0o600)
    assert (code, note) == (0, "")
    assert not path.exists()


def test_clear_vanished_lock_reports_retry(tmp_path):
    code, note = lock._clear(tmp_path / "lock.json", "pid", "loop-b")
    assert code == 2
    assert "vanished" in note and "acquire again" in note


def test_release_paths(tmp_path):
    assert lock.release(tmp_path, holder="loop-b") == (0, "")
    write_lock(tmp_path, make_rec(holder="loop-b"))
    assert lock.release(tmp_path, holder="loop-b") == (0, "")
    assert not (tmp_path / "lock.json").exists()
    assert lock.release(tmp_path, force=True) == (0, "")


def test_release_mismatch_refuses_and_keeps(tmp_path):
    path = write_lock(tmp_path, make_rec(holder="loop-a"))
    code, note = lock.release(tmp_path, holder="loop-b")
    assert code == 2
    assert "loop-a" in note
    assert path.exists()


def test_release_force_beats_mismatch(tmp_path):
    write_lock(tmp_path, make_rec(holder="loop-a"))
    assert lock.release(tmp_path, holder="loop-b", force=True) == (0, "")
    assert not (tmp_path / "lock.json").exists()


def test_release_corrupt_needs_force(tmp_path):
    write_raw(tmp_path, "nope")
    code, note = lock.release(tmp_path, holder="loop-b")
    assert code == 2
    assert "does not parse" in note and "--force" in note
    assert lock.release(tmp_path, force=True) == (0, "")


def test_examine_foreign_host_fresh(tmp_path):
    write_lock(tmp_path, make_rec(host="elsewhere"))
    code, note = lock.examine(tmp_path, holder=None, probe=probe_dead,
                              host="h1", boot_id="b1", now=NOW)
    assert code == 2
    assert "loop-20261107-a" in note


def test_examine_paths(tmp_path):
    assert lock.examine(tmp_path, holder=None, probe=probe_ok, host="h1",
                        boot_id="b1", now=NOW) == (0, "")
    write_lock(tmp_path, make_rec(pid=4242))
    code, note = lock.examine(tmp_path, holder=None, probe=probe_ok,
                              host="h1", boot_id="b1", now=NOW)
    assert code == 2 and "loop-20261107-a" in note
    code, note = lock.examine(tmp_path, holder="loop-20261107-a", probe=probe_ok,
                              host="h1", boot_id="b1", now=NOW)
    assert (code, note) == (0, "")


def test_examine_own_caller_pid(tmp_path):
    write_lock(tmp_path, make_rec(pid=777))
    code, note = lock.examine(tmp_path, holder=None, probe=probe_ok,
                              host="h1", boot_id="b1", now=NOW,
                              caller_pid=777)
    assert (code, note) == (0, "")


def test_examine_stale_reports_and_proceeds(tmp_path):
    write_lock(tmp_path, make_rec(pid=4242))
    code, note = lock.examine(tmp_path, holder=None, probe=probe_dead,
                              host="h1", boot_id="b1", now=NOW)
    assert code == 0
    assert note == (
        "process_issues: the lock is stale (pid); the scan proceeds, "
        "and acquire clears it"
    )


def test_examine_anchorless_ages_out(tmp_path):
    write_lock(tmp_path, make_rec(pid=None, pid_start=None, acquired_at=OLD))
    code, note = lock.examine(tmp_path, holder=None, probe=probe_dead,
                              host="h1", boot_id="b1", now=NOW)
    assert code == 0
    assert "age" in note


def test_examine_unreadable_refuses(tmp_path):
    path = write_lock(tmp_path, make_rec())
    path.chmod(0o000)
    try:
        code, note = lock.examine(tmp_path, holder=None, probe=probe_ok,
                                  host="h1", boot_id="b1", now=NOW)
    finally:
        path.chmod(0o600)
    assert code == 2 and "cannot read" in note


def test_resolve_state_dir_from_git_common_dir(tmp_path):
    fake = lambda args: (0, "/repo/main/.git\n", "")
    resolved = lock.resolve_state_dir(tmp_path, fake)
    assert str(resolved) == "/repo/main/.process_issues"


def test_resolve_state_dir_falls_back(tmp_path):
    fake = lambda args: (1, "", "fatal: not a git repository")
    assert lock.resolve_state_dir(tmp_path, fake) == tmp_path / ".process_issues"
    empty = lambda args: (0, "", "")
    assert lock.resolve_state_dir(tmp_path, empty) == tmp_path / ".process_issues"


def test_probe_live_paths():
    assert lock.probe_live(None, "1") == "pid"
    assert lock.probe_live(True, "1") == "pid"
    assert lock.probe_live("5", "1") == "pid"
    assert lock.probe_live(0, "1") == "pid"
    mine = os.getpid()
    assert lock.probe_live(mine, lock.start_time(mine)) is None
    assert lock.probe_live(mine, "999999") == "start"


def test_probe_live_dead_pid():
    assert lock.probe_live(dead_pid(), "1") == "pid"


def test_stat_fields_real():
    fields = lock._stat_fields(os.getpid())
    assert fields is not None
    comm, ppid, start = fields
    assert isinstance(ppid, int)
    assert start.isdigit()
    assert lock.start_time(os.getpid()) == start
    assert lock._stat_fields(2 ** 24) is None


def test_stat_fields_match_an_independent_parse():
    pid = os.getpid()
    data = open(f"/proc/{pid}/stat", "rb").read().decode()
    comm = data.split("(", 1)[1].rsplit(")", 1)[0]
    rest = data.rsplit(")", 1)[1].split()
    assert lock._stat_fields(pid) == (comm, int(rest[1]), rest[19])


def test_probe_live_pid_one_is_alive():
    assert lock.probe_live(1, lock.start_time(1)) is None


def test_session_anchor_stops_before_pid_one():
    chain = {3: ("bash", 1, "2"), 1: ("claude", 0, "9")}
    assert lock.session_anchor(3, chain.get) == (None, None)


def test_run_git_error_carries_a_nonzero_code():
    code, out, err = cli.run_git(["definitely-not-a-command-xyz"])
    assert code != 0
    assert "git" in err


def test_scan_of_the_own_session_proceeds(tmp_path, capsys):
    anchor = lock.session_anchor()[0]
    if anchor is None:
        import pytest

        pytest.skip("no session anchor on this host")
    write_lock(tmp_path / ".process_issues",
               fresh_rec(holder="loop-x", pid=anchor,
                         pid_start=lock.start_time(anchor)))
    fake = FakeGh([(0, ISSUES, ""), (0, PRS, "")])
    code = cli.main(["scan"], runner=fake, repo_root=str(tmp_path),
                    git_runner=lambda args: (1, "", ""))
    out = capsys.readouterr().out
    assert code == 0
    assert fake.index == 2
    assert "9" in out


def test_session_anchor_walks_to_the_harness():
    chain = {
        102: ("python3", 101, "9"),
        101: ("bash", 100, "8"),
        100: ("claude", 99, "4"),
        99: ("tmux: server", 1, "3"),
    }
    assert lock.session_anchor(102, chain.get) == (100, "4")


def test_session_anchor_without_harness_gives_none():
    chain = {102: ("python3", 101, "9"), 101: ("bash", 1, "8")}
    assert lock.session_anchor(102, chain.get) == (None, None)


def test_session_anchor_survives_a_cycle():
    chain = {5: ("sh", 6, "1"), 6: ("sh", 5, "1")}
    assert lock.session_anchor(5, chain.get) == (None, None)


def test_session_anchor_is_stable_in_process():
    assert lock.session_anchor() == lock.session_anchor()


def test_this_host_and_boot_shapes():
    assert isinstance(lock.this_host(), str)
    assert lock.this_boot_id() is None or isinstance(lock.this_boot_id(), str)


def holder_of(root):
    """Read the holder of the lock file under the state dir."""
    return json.loads((root / "lock.json").read_text())["holder"]


def fresh_rec(holder="loop-live", pid=None, pid_start=None):
    """Return a record that looks fresh on this host and boot."""
    if pid is None:
        pid = os.getpid()
    if pid_start is None:
        pid_start = lock.start_time(pid)
    return make_rec(holder=holder, host=lock.this_host(),
                    boot_id=lock.this_boot_id(), pid=pid, pid_start=pid_start,
                    acquired_at=datetime.now(timezone.utc).isoformat())


def dead_pid():
    """Return one pid that no longer runs."""
    proc = subprocess.Popen(["true"])
    proc.wait()
    return proc.pid


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
    {"number": 9, "title": "t", "createdAt": "2026-11-07T00:00:00Z",
     "labels": []},
])
PRS = json.dumps([])


def test_scan_refuses_fresh_foreign_and_skips_gh(tmp_path, capsys):
    write_lock(tmp_path / ".process_issues", fresh_rec(holder="loop-live"))
    fake = FakeGh([(0, ISSUES, "")])
    code = cli.main(["scan"], runner=fake, repo_root=str(tmp_path),
                    git_runner=lambda args: (1, "", ""))
    err = capsys.readouterr().err
    assert code == 2
    assert "loop-live" in err
    assert fake.index == 0


def test_scan_holder_label_proceeds(tmp_path, capsys):
    write_lock(tmp_path / ".process_issues", fresh_rec(holder="loop-live"))
    fake = FakeGh([(0, ISSUES, ""), (0, PRS, "")])
    code = cli.main(["scan", "--holder", "loop-live"], runner=fake,
                    repo_root=str(tmp_path),
                    git_runner=lambda args: (1, "", ""))
    out = capsys.readouterr().out
    assert code == 0
    assert "9" in out


def test_scan_reports_stale_and_proceeds(tmp_path, capsys):
    path = write_lock(tmp_path / ".process_issues",
                      fresh_rec(pid=dead_pid(), pid_start="1"))
    before = path.read_bytes()
    fake = FakeGh([(0, ISSUES, ""), (0, PRS, "")])
    code = cli.main(["scan"], runner=fake, repo_root=str(tmp_path),
                    git_runner=lambda args: (1, "", ""))
    err = capsys.readouterr().err
    assert code == 0
    assert "stale" in err
    assert fake.index == 2
    assert path.read_bytes() == before


def test_scan_reports_corrupt_and_proceeds(tmp_path, capsys):
    write_raw(tmp_path / ".process_issues", "{oops")
    fake = FakeGh([(0, ISSUES, ""), (0, PRS, "")])
    code = cli.main(["scan"], runner=fake, repo_root=str(tmp_path),
                    git_runner=lambda args: (1, "", ""))
    err = capsys.readouterr().err
    assert code == 0
    assert "corrupt" in err
    assert fake.index == 2


def test_scan_reports_old_age_and_proceeds(tmp_path, capsys):
    old_rec = fresh_rec(holder="loop-old")
    old_rec["acquired_at"] = OLD
    write_lock(tmp_path / ".process_issues", old_rec)
    fake = FakeGh([(0, ISSUES, ""), (0, PRS, "")])
    code = cli.main(["scan"], runner=fake, repo_root=str(tmp_path),
                    git_runner=lambda args: (1, "", ""))
    err = capsys.readouterr().err
    assert code == 0
    assert "age" in err
    assert fake.index == 2


def test_scan_without_lock_proceeds(tmp_path, capsys):
    fake = FakeGh([(0, ISSUES, ""), (0, PRS, "")])
    code = cli.main(["scan", "--json"], runner=fake, repo_root=str(tmp_path),
                    git_runner=lambda args: (1, "", ""))
    out = capsys.readouterr().out
    assert code == 0
    assert json.loads(out)[0]["number"] == 9


def test_acquire_and_release_cli_round_trip(tmp_path, capsys):
    common = lambda args: (1, "", "")
    code = cli.main(["acquire", "--holder", "loop-x"], repo_root=str(tmp_path),
                    git_runner=common)
    assert code == 0
    assert holder_of(tmp_path / ".process_issues") == "loop-x"
    code = cli.main(["scan", "--holder", "loop-x"], repo_root=str(tmp_path),
                    git_runner=common)
    assert code == 0
    code = cli.main(["release", "--holder", "loop-x"], repo_root=str(tmp_path),
                    git_runner=common)
    assert code == 0
    assert not (tmp_path / ".process_issues" / "lock.json").exists()


def test_release_mismatch_cli_refuses(tmp_path):
    common = lambda args: (1, "", "")
    cli.main(["acquire", "--holder", "loop-x"], repo_root=str(tmp_path),
             git_runner=common)
    code = cli.main(["release", "--holder", "loop-y"], repo_root=str(tmp_path),
                    git_runner=common)
    assert code == 2
    assert holder_of(tmp_path / ".process_issues") == "loop-x"


def test_release_force_cli_clears(tmp_path):
    common = lambda args: (1, "", "")
    cli.main(["acquire", "--holder", "loop-x"], repo_root=str(tmp_path),
             git_runner=common)
    code = cli.main(["release", "--force"], repo_root=str(tmp_path),
                    git_runner=common)
    assert code == 0
    assert not (tmp_path / ".process_issues" / "lock.json").exists()


def test_acquire_with_force_exits_64(tmp_path):
    common = lambda args: (1, "", "")
    code = cli.main(["acquire", "--holder", "loop-x", "--force"],
                    repo_root=str(tmp_path), git_runner=common)
    assert code == 64
    assert not (tmp_path / ".process_issues" / "lock.json").exists()


def test_usage_errors_exit_64(tmp_path):
    common = lambda args: (1, "", "")
    assert cli.main(["acquire"], repo_root=str(tmp_path),
                    git_runner=common) == 64
    assert cli.main(["release"], repo_root=str(tmp_path),
                    git_runner=common) == 64
    assert cli.main(["scan", "--nope"], repo_root=str(tmp_path),
                    git_runner=common) == 64
    assert cli.main(["frobnicate"], repo_root=str(tmp_path),
                    git_runner=common) == 64
    assert cli.main(["--help"], repo_root=str(tmp_path),
                    git_runner=common) == 0


def test_acquire_cli_uses_the_session_anchor(tmp_path):
    common = lambda args: (1, "", "")
    code = cli.main(["acquire", "--holder", "loop-x"], repo_root=str(tmp_path),
                    git_runner=common)
    assert code == 0
    rec = json.loads((tmp_path / ".process_issues" / "lock.json").read_text())
    anchor_pid, anchor_start = lock.session_anchor()
    if anchor_pid is None:
        assert rec["pid"] is None
    else:
        assert rec["pid"] == anchor_pid
        assert rec["pid_start"] == anchor_start
