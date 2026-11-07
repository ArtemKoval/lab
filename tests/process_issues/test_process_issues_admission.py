"""Behavior tests for the admission gate in process_issues."""

import json

import pytest

from process_issues import authors, cli, core


def test_admitted_paths():
    assert core.admitted("ArtemKoval", ["ArtemKoval"]) is True
    assert core.admitted("ArtemKoval", ["artemkoval"]) is True
    assert core.admitted("artemkoval", ["ArtemKoval"]) is True
    assert core.admitted("stranger", ["ArtemKoval"]) is False
    assert core.admitted("ArtemKoval", []) is False


def test_admitted_refuses_bad_logins_and_bots():
    assert core.admitted(None, ["ArtemKoval"]) is False
    assert core.admitted("", ["ArtemKoval"]) is False
    assert core.admitted(42, ["ArtemKoval"]) is False
    assert core.admitted("helper[bot]", ["helper[bot]"]) is False
    assert core.admitted("HELPER[BOT]", ["helper[bot]"]) is False


def test_load_authors_happy_paths(tmp_path):
    path = tmp_path / "authors.json"
    path.write_text('{"allowed_authors": ["ArtemKoval"], "extra": 1}',
                    encoding="utf-8")
    assert authors.load_authors(path) == ["ArtemKoval"]
    path.write_text('{"allowed_authors": []}', encoding="utf-8")
    assert authors.load_authors(path) == []


def test_load_authors_wrong_shapes_name_the_path(tmp_path):
    path = tmp_path / "authors.json"
    cases = [
        "not json {",
        '["ArtemKoval"]',
        '{"author": ["ArtemKoval"]}',
        '{"allowed_authors": "ArtemKoval"}',
        '{"allowed_authors": [1]}',
    ]
    for raw in cases:
        path.write_text(raw, encoding="utf-8")
        with pytest.raises(authors.AuthorsError) as err:
            authors.load_authors(path)
        assert str(path) in str(err.value)
    with pytest.raises(authors.AuthorsError) as err:
        authors.load_authors(tmp_path / "missing.json")
    assert "missing.json" in str(err.value)


AUTHOR_OK = {"author": {"login": "ArtemKoval"}}


def queue_fixture():
    """Return one issue list with foreign, allowed, and bot authors."""
    return [
        {"number": 30, "title": "stranger work", "createdAt":
         "2026-11-07T00:00:00Z", "labels": [],
         "author": {"login": "stranger"}},
        {"number": 31, "title": "stranger handover", "createdAt":
         "2026-11-07T01:00:00Z", "labels": [{"name": "handover"}],
         "author": {"login": "stranger"}},
        {"number": 32, "title": "stranger blocked", "createdAt":
         "2026-11-07T02:00:00Z", "labels": [{"name": "blocked"}],
         "author": {"login": "stranger"}},
        {"number": 33, "title": "operator blocked", "createdAt":
         "2026-11-07T03:00:00Z", "labels": [{"name": "blocked"}],
         "author": {"login": "ArtemKoval"}},
        {"number": 34, "title": "listed bot", "createdAt":
         "2026-11-07T04:00:00Z", "labels": [],
         "author": {"login": "helper[bot]"}},
        {"number": 35, "title": "case variant", "createdAt":
         "2026-11-07T05:00:00Z", "labels": [],
         "author": {"login": "artemkoval"}},
        {"number": 36, "title": "no author", "createdAt":
         "2026-11-07T06:00:00Z", "labels": []},
    ]


def build(tmp_path, issues):
    """Build the queue with the operator allowed list."""
    return cli.build_queue(issues, [], str(tmp_path), ["ArtemKoval"])


def test_queue_refuses_above_the_labels(tmp_path):
    queue = build(tmp_path, queue_fixture())
    states = {entry["number"]: entry["state"] for entry in queue}
    actions = {entry["number"]: entry["action"] for entry in queue}
    assert states[30] == "refused" and actions[30] == "none"
    assert states[31] == "refused"
    assert states[32] == "refused"
    assert states[33] == "blocked"
    assert states[34] == "refused"
    assert states[35] == "propose"
    assert states[36] == "refused"


def test_queue_carries_the_author_login(tmp_path):
    queue = build(tmp_path, queue_fixture())
    authors_by_number = {entry["number"]: entry["author"] for entry in queue}
    assert authors_by_number[30] == "stranger"
    assert authors_by_number[33] == "ArtemKoval"
    assert authors_by_number[36] is None


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


def no_git(args):
    """Runner that refuses the git call."""
    return 1, "", "tests use no real git"


ISSUES_JSON = json.dumps(queue_fixture())
PRS_JSON = json.dumps([])


def test_scan_fetch_argv_pins_the_field_list(tmp_path, capsys):
    seen = []

    def recorder(args):
        seen.append(args)
        if len(seen) == 1:
            return 0, ISSUES_JSON, ""
        return 0, PRS_JSON, ""

    code = cli.main(["scan", "--json"], runner=recorder,
                    repo_root=str(tmp_path), git_runner=no_git)
    assert code == 0
    assert "author" in seen[0][-1].split(",")
    assert "author" in cli.ISSUE_FIELDS.split(",")


def test_status_fetch_argv_pins_the_field_list(tmp_path, capsys):
    seen = []

    def recorder(args):
        seen.append(args)
        if len(seen) == 1:
            return 0, "tokentoken\n", ""
        return 0, json.dumps([]), ""

    code = cli.main(["status"], runner=recorder, repo_root=str(tmp_path),
                    git_runner=no_git)
    assert code == 1
    assert "author" in seen[1][-1].split(",")


def test_scan_config_failure_exits_2_with_the_path(tmp_path, capsys):
    broken = tmp_path / "broken-authors.json"
    broken.write_text("not json {", encoding="utf-8")
    monkey_target = broken
    original = authors.AUTHORS_PATH
    authors.AUTHORS_PATH = monkey_target
    try:
        fake = FakeGh([])
        code = cli.main(["scan", "--json"], runner=fake,
                        repo_root=str(tmp_path), git_runner=no_git)
    finally:
        authors.AUTHORS_PATH = original
    captured = capsys.readouterr()
    assert code == 2
    assert "broken-authors.json" in captured.err
    assert captured.out == ""
    assert fake.index == 0


def test_status_config_row_reports_component_error(tmp_path, capsys):
    broken = tmp_path / "broken-authors.json"
    broken.write_text('{"allowed_authors": "nope"}', encoding="utf-8")
    original = authors.AUTHORS_PATH
    authors.AUTHORS_PATH = broken
    try:
        fake = FakeGh([(0, "tokentoken\n", "")])
        code = cli.main(["status"], runner=fake, repo_root=str(tmp_path),
                        git_runner=no_git)
    finally:
        authors.AUTHORS_PATH = original
    captured = capsys.readouterr()
    assert code == 2
    assert "broken-authors.json" in captured.err
    assert fake.index == 1


def test_status_json_config_level(tmp_path, capsys):
    broken = tmp_path / "broken-authors.json"
    broken.write_text("not json {", encoding="utf-8")
    original = authors.AUTHORS_PATH
    authors.AUTHORS_PATH = broken
    try:
        code = cli.main(["status", "--json"],
                        runner=FakeGh([(0, "tokentoken\n", "")]),
                        repo_root=str(tmp_path), git_runner=no_git)
    finally:
        authors.AUTHORS_PATH = original
    payload = json.loads(capsys.readouterr().out)
    assert payload["level"] == "config" and payload["code"] == 2


def test_status_refused_blocked_issue_stays_off_the_rows(tmp_path, capsys):
    foreign_blocked = json.dumps([
        {"number": 32, "title": "stranger blocked", "labels":
         [{"name": "blocked"}], "author": {"login": "stranger"}},
    ])
    fake = FakeGh([(0, "tokentoken\n", ""), (0, foreign_blocked, "")])
    code = cli.main(["status"], runner=fake, repo_root=str(tmp_path),
                    git_runner=no_git)
    assert code == 1
    assert fake.index == 2


def test_shipped_list_carries_the_operator(monkeypatch):
    names = authors.load_authors()
    assert "ArtemKoval" in names
