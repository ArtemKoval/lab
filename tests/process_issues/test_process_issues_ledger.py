"""Behavior tests for the write-ahead ledger in process_issues."""

import json

from process_issues import cli, ledger


def write_records(path, rows):
    """Append raw records or raw lines to a ledger file."""
    with open(path, "a", encoding="utf-8") as handle:
        for row in rows:
            if isinstance(row, str):
                handle.write(row + "\n")
            else:
                handle.write(json.dumps(row) + "\n")


def intent(marker, kind="comment", key="15"):
    """Return one intent record."""
    return {"event": "intent", "id": marker, "kind": kind, "key": key,
            "at": "2026-11-07T20:00:00+00:00"}


def confirmed(marker):
    """Return one confirmation record."""
    return {"event": "confirmed", "id": marker,
            "at": "2026-11-07T20:01:00+00:00"}


def fixed_rng():
    """Return a random source that yields fixed values in a cycle."""
    values = iter([0.0, 0.5, 0.25, 0.75, 0.1, 0.9, 0.3, 0.7])

    def rng():
        try:
            return next(values)
        except StopIteration:
            return 0.5

    return rng


def test_new_marker_fresh_per_call():
    first = ledger.new_marker(set(), now=1_700_000_000.0, rng=fixed_rng())
    second = ledger.new_marker({first}, now=1_700_000_000.0,
                               rng=fixed_rng())
    assert first.startswith("loop-")
    assert first != second
    assert second.startswith("loop-")


def test_new_marker_stamp_and_suffix_follow_the_inputs():
    marker = ledger.new_marker(set(), now=1_700_000_000.0, rng=lambda: 0.5)
    assert marker == "loop-202311142213-8000"


def test_new_marker_regeneration_crosses_the_minute():
    cycle = iter([0.0, 0.5])
    marker = ledger.new_marker({"loop-202311142212-0000"},
                               now=1_699_999_979.0,
                               rng=lambda: next(cycle))
    assert marker == "loop-202311142213-8000"


def test_new_marker_regenerates_on_collision():
    marker = ledger.new_marker({"loop-202311142213-0000"},
                               now=1_700_000_000.0, rng=lambda: 0.0)
    assert marker == "loop-202311142214-0000"


def test_append_record_guards_the_newline(tmp_path):
    path = tmp_path / "ledger.jsonl"
    ledger.append_record(path, intent("loop-a"))
    with open(path, "ab") as handle:
        handle.write(b'{"event": "intent", "id": "torn"')  # a torn line
    ledger.append_record(path, intent("loop-b"))
    records, notes = ledger.read_records(path)
    assert [row["id"] for row in records] == ["loop-a", "loop-b"]
    assert len(notes) == 1 and "line 2" in notes[0]


def test_append_record_creates_nested_dirs(tmp_path):
    path = tmp_path / "deep" / "state" / "ledger.jsonl"
    ledger.append_record(path, intent("loop-a"))
    records, notes = ledger.read_records(path)
    assert [row["id"] for row in records] == ["loop-a"]
    assert notes == []


def test_read_records_shapes(tmp_path):
    path = tmp_path / "ledger.jsonl"
    assert ledger.read_records(path) == ([], [])
    write_records(path, [intent("loop-a"), confirmed("loop-a"),
                         "not json {", '{"event": "unknown-shape"}', "   ",
                         '{"event": "confirmed"}',
                         '{"event": "confirmed", "id": 42, "at": "t"}'])
    records, notes = ledger.read_records(path)
    assert [row["id"] for row in records] == ["loop-a", "loop-a"]
    assert notes == ["skipped ledger line 3", "skipped ledger line 4",
                     "skipped ledger line 6", "skipped ledger line 7"]


def test_read_records_unreadable_raises(tmp_path):
    path = tmp_path / "ledger.jsonl"
    write_records(path, [intent("loop-a")])
    path.chmod(0o000)
    try:
        raised = False
        try:
            ledger.read_records(path)
        except ledger.LedgerError:
            raised = True
    finally:
        path.chmod(0o600)
    assert raised is True


def test_pending_view_flags_and_orders():
    records = [
        intent("loop-a", "comment", "15"),
        intent("loop-b", "comment", "15"),
        confirmed("loop-b"),
        intent("loop-c", "label", "15:staging"),
        intent("loop-d", "comment", "16"),
    ]
    rows = ledger.pending_view(records)
    assert [row["id"] for row in rows] == ["loop-a", "loop-c", "loop-d"]
    assert rows[0]["superseded"] is False
    assert rows[1]["superseded"] is False
    assert rows[2]["superseded"] is False


def test_pending_view_supersedes_within_a_group():
    records = [
        intent("loop-a", "comment", "15"),
        intent("loop-b", "comment", "15"),
    ]
    rows = ledger.pending_view(records)
    assert rows[0]["superseded"] is True
    assert rows[1]["superseded"] is False


def test_pending_view_drops_confirmed_intents():
    records = [intent("loop-a"), confirmed("loop-a")]
    assert ledger.pending_view(records) == []


def no_git(args):
    """Runner that refuses the git call."""
    return 1, "", "tests use no real git"


def run_ledger(tmp_path, argv):
    """Run the ledger CLI rooted at tmp_path."""
    code = cli.main(list(argv), runner=FakeGh([]), repo_root=str(tmp_path),
                    git_runner=no_git)
    return code


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


def test_cli_write_confirm_pending_round_trip(tmp_path, capsys):
    code = run_ledger(tmp_path, ["ledger", "write", "--kind", "comment",
                                 "--key", "15"])
    assert code == 0
    marker = capsys.readouterr().out.strip()
    assert marker.startswith("loop-")
    code = run_ledger(tmp_path, ["ledger", "confirm", "--id", marker])
    assert code == 0
    code = run_ledger(tmp_path, ["ledger", "pending", "--json"])
    assert code == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows == []


def test_cli_pending_flags_superseded(tmp_path, capsys):
    run_ledger(tmp_path, ["ledger", "write", "--kind", "comment",
                          "--key", "15"])
    capsys.readouterr()
    run_ledger(tmp_path, ["ledger", "write", "--kind", "comment",
                          "--key", "15"])
    capsys.readouterr()
    code = run_ledger(tmp_path, ["ledger", "pending", "--json"])
    rows = json.loads(capsys.readouterr().out)
    assert code == 0
    assert len(rows) == 2
    assert rows[0]["id"] != rows[1]["id"]
    assert set(rows[0]) == {"id", "kind", "key", "at", "superseded"}
    assert rows[0]["superseded"] is True
    assert rows[1]["superseded"] is False


def test_cli_unreadable_store_exits_2(tmp_path, capsys):
    path = tmp_path / ".process_issues" / "ledger.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    path.chmod(0o000)
    try:
        code = run_ledger(tmp_path, ["ledger", "pending"])
    finally:
        path.chmod(0o600)
    captured = capsys.readouterr()
    assert code == 2
    assert "cannot read the ledger" in captured.err


def test_cli_stray_action_exits_64(tmp_path):
    assert run_ledger_stray(tmp_path, ["scan", "write"]) == 64
    assert run_ledger_stray(tmp_path, ["status", "write"]) == 64


def run_ledger_stray(tmp_path, argv):
    """Run the CLI with the real scan path stubbed by a fake runner."""
    code = cli.main(list(argv), runner=FakeGh([]), repo_root=str(tmp_path),
                    git_runner=no_git)
    return code


def test_cli_second_write_draws_the_note(tmp_path, capsys):
    run_ledger(tmp_path, ["ledger", "write", "--kind", "comment",
                          "--key", "15"])
    code = run_ledger(tmp_path, ["ledger", "write", "--kind", "comment",
                                 "--key", "15"])
    captured = capsys.readouterr()
    assert code == 0
    assert "already carries a live pending intent" in captured.err


def test_cli_confirm_unknown_id_exits_2(tmp_path, capsys):
    code = run_ledger(tmp_path, ["ledger", "confirm", "--id", "loop-none"])
    captured = capsys.readouterr()
    assert code == 2
    assert "loop-none" in captured.err


def test_cli_second_confirm_is_a_no_op(tmp_path, capsys):
    run_ledger(tmp_path, ["ledger", "write", "--kind", "comment",
                          "--key", "15"])
    marker = capsys.readouterr().out.strip()
    run_ledger(tmp_path, ["ledger", "confirm", "--id", marker])
    before = (tmp_path / ".process_issues" / "ledger.jsonl").read_text()
    code = run_ledger(tmp_path, ["ledger", "confirm", "--id", marker])
    after = (tmp_path / ".process_issues" / "ledger.jsonl").read_text()
    assert code == 0
    assert before == after


def test_cli_missing_store_gives_empty_pending(tmp_path, capsys):
    code = run_ledger(tmp_path, ["ledger", "pending", "--json"])
    captured = capsys.readouterr()
    assert code == 0
    assert json.loads(captured.out) == []


def test_cli_usage_errors_exit_64(tmp_path):
    assert run_ledger(tmp_path, ["ledger"]) == 64
    assert run_ledger(tmp_path, ["ledger", "write"]) == 64
    assert run_ledger(tmp_path, ["ledger", "write", "--kind", "nope",
                                 "--key", "1"]) == 64
    assert run_ledger(tmp_path, ["ledger", "write", "--kind", "comment"]) == 64
    assert run_ledger(tmp_path, ["ledger", "confirm"]) == 64
    assert run_ledger(tmp_path, ["ledger", "frobnicate"]) == 64


def test_cli_pending_plain_rows_and_skip_notes(tmp_path, capsys):
    path = tmp_path / ".process_issues" / "ledger.jsonl"
    ledger.append_record(path, intent("loop-a", "comment", "15"))
    ledger.append_record(path, intent("loop-b", "label", "15:staging"))
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("not json {\n")
    code = run_ledger(tmp_path, ["ledger", "pending"])
    captured = capsys.readouterr()
    assert code == 0
    lines = captured.out.strip().split("\n")
    assert len(lines) == 2
    assert lines[0].startswith("loop-a\tcomment\t15\t")
    assert "\tlive" in lines[0]
    assert "superseded" not in lines[0]
    assert "skipped ledger line 3" in captured.err
