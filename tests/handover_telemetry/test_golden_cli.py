"""Golden tests for the command line: the pinned stdout text for the
build and sessions commands, the pinned gh invocation, the pinned
help text, and the pinned error messages."""

import os
import subprocess
from pathlib import Path

import pytest

from golden_data import GOLDEN_JSON, GOLDEN_MD, HOOK_LOG, HOST, SESSION_DIR

from handover_telemetry import cli, machine

HELP_MAIN = """\
usage: handover_telemetry [-h] {build,sessions} ...

The command line for handover_telemetry. Subcommands build and sessions. The
build reads one session transcript plus the cc-logging hook log, and renders a
redacted telemetry report as markdown or JSON. The sessions listing names the
candidate transcripts. Exit 0 on success and 2 on operational failure. The gh
issue path runs only behind --create; every other path stays offline.

positional arguments:
  {build,sessions}
    build           render the telemetry report for one session
    sessions        list the session transcripts

options:
  -h, --help        show this help message and exit
"""

HELP_BUILD = """\
usage: handover_telemetry build [-h] [--project-dir PROJECT_DIR]
                                [--transcript TRANSCRIPT] [--session SESSION]
                                [--repo REPO] [--prices PRICES] [--out OUT]
                                [--json] [--create]

options:
  -h, --help            show this help message and exit
  --project-dir PROJECT_DIR
                        Claude Code project directory
  --transcript TRANSCRIPT
                        path to the session transcript
  --session SESSION     session id or transcript file stem
  --repo REPO           repository root
  --prices PRICES       override the packaged price table
  --out OUT             write the report to this file
  --json                emit JSON with GenAI names
  --create              open the issue via gh
"""

HELP_SESSIONS = """\
usage: handover_telemetry sessions [-h] [--project-dir PROJECT_DIR]

options:
  -h, --help            show this help message and exit
  --project-dir PROJECT_DIR
                        project directory
"""

NO_COMMAND_ERROR = """\
usage: handover_telemetry [-h] {build,sessions} ...
handover_telemetry: error: the following arguments are required: command
"""

SESSIONS_LISTING = """\
empty.jsonl  unknown -> unknown  models: none
main.jsonl  2026-10-29T10:00:00.000Z -> 2026-10-29T10:00:20.000Z  models: glm-5.3-flash
two.jsonl  2026-01-01T00:00:01Z -> 2026-01-01T00:00:03Z  models: a-model, z-model
"""

DERIVED_BASH_ROW = "| 1 | primary | Bash | 2026-10-29T10:00:05.000Z | 2000 | 1 |"

TWO_MODEL_LINES = "\n".join(
    [
        '{"type": "assistant", "sessionId": "two", "timestamp": "2026-01-01T00:00:01Z",'
        ' "message": {"id": "m1", "model": "z-model", "usage": {}, "content": []}}',
        '{"type": "assistant", "sessionId": "two", "timestamp": "2026-01-01T00:00:02Z",'
        ' "message": {"id": "m2", "model": "a-model", "usage": {}, "content": []}}',
        '{"type": "assistant", "sessionId": "two", "timestamp": "2026-01-01T00:00:03Z",'
        ' "message": {"id": "m3", "model": "a-model", "usage": {}, "content": []}}',
    ]
) + "\n"


class _Completed:
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture()
def project(tmp_path) -> Path:
    main = tmp_path / "main.jsonl"
    main.write_text((SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    sub = tmp_path / "sess-1" / "subagents"
    sub.mkdir(parents=True)
    (sub / "agent-42.jsonl").write_text(
        (SESSION_DIR / "sess-1" / "subagents" / "agent-42.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def repo(tmp_path) -> Path:
    root = tmp_path / "repo"
    (root / ".cc_logging").mkdir(parents=True)
    (root / ".cc_logging" / "main.jsonl").write_text(
        HOOK_LOG.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return root


@pytest.fixture()
def stub_host(monkeypatch):
    monkeypatch.setattr(machine, "collect", lambda repo=None: dict(HOST))


def _build(project: Path, repo: Path, *extra: str) -> list[str]:
    return [
        "build",
        "--project-dir",
        str(project),
        "--transcript",
        str(project / "main.jsonl"),
        "--repo",
        str(repo),
        *extra,
    ]


def test_build_stdout_is_the_pinned_markdown(project, repo, stub_host, capsys):
    assert cli.main(_build(project, repo)) == 0
    assert capsys.readouterr().out == GOLDEN_MD


def test_build_json_stdout_is_the_pinned_json(project, repo, stub_host, capsys):
    assert cli.main(_build(project, repo, "--json")) == 0
    assert capsys.readouterr().out == GOLDEN_JSON


def test_build_without_a_hook_log_derives_the_duration(project, tmp_path, stub_host, capsys):
    bare = tmp_path / "bare-repo"
    bare.mkdir()
    assert cli.main(_build(project, bare)) == 0
    assert DERIVED_BASH_ROW in capsys.readouterr().out


def test_out_file_carries_the_pinned_markdown(project, repo, stub_host, tmp_path, capsys):
    target = tmp_path / "report.md"
    assert cli.main(_build(project, repo, "--out", str(target))) == 0
    assert target.read_text(encoding="utf-8") == GOLDEN_MD
    assert capsys.readouterr().out == f"wrote {target}\n"


def test_missing_transcript_message_is_exact(tmp_path, capsys):
    missing = tmp_path / "none.jsonl"
    code = cli.main(["build", "--project-dir", str(tmp_path), "--transcript", str(missing)])
    out, err = capsys.readouterr()
    assert code == 2
    assert err == f"handover_telemetry: no transcript at {missing}\n"
    assert out == ""


def test_missing_project_dir_message_is_exact(tmp_path, capsys):
    absent = tmp_path / "gone"
    code = cli.main(["sessions", "--project-dir", str(absent)])
    out, err = capsys.readouterr()
    assert code == 2
    assert err == f"handover_telemetry: no project directory at {absent}\n"
    assert out == ""


def test_corrupt_price_table_message_is_exact(project, repo, stub_host, tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("]", encoding="utf-8")
    code = cli.main(_build(project, repo, "--prices", str(bad)))
    out, err = capsys.readouterr()
    assert code == 2
    assert out == ""
    assert (
        err
        == f"handover_telemetry: cannot read price table {bad}: Expecting value: line 1 column 1 (char 0)\n"
    )


def test_absent_price_table_message_is_exact(project, repo, stub_host, tmp_path, capsys):
    absent = tmp_path / "none.json"
    code = cli.main(_build(project, repo, "--prices", str(absent)))
    err = capsys.readouterr().err
    assert code == 2
    assert err == (
        f"handover_telemetry: cannot read price table {absent}: "
        f"[Errno 2] No such file or directory: '{absent}'\n"
    )


def test_sessions_listing_is_the_pinned_text(tmp_path, capsys):
    (tmp_path / "empty.jsonl").write_text("{}\n", encoding="utf-8")
    (tmp_path / "main.jsonl").write_text(
        (SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8"
    )
    two = tmp_path / "two.jsonl"
    two.write_text(TWO_MODEL_LINES, encoding="utf-8")
    assert cli.main(["sessions", "--project-dir", str(tmp_path)]) == 0
    assert capsys.readouterr().out == SESSIONS_LISTING


def test_session_flag_selects_the_named_transcript_over_the_newest(tmp_path, capsys):
    import os

    named = tmp_path / "named.jsonl"
    named.write_text(
        '{"type": "mode", "sessionId": "named-one"}\n', encoding="utf-8"
    )
    newest = tmp_path / "newest.jsonl"
    newest.write_text(
        '{"type": "mode", "sessionId": "newest-one"}\n', encoding="utf-8"
    )
    future = os.path.getmtime(newest) + 100
    os.utime(newest, (future, future))
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(tmp_path),
            "--session",
            "named",
            "--repo",
            str(tmp_path),
            "--json",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert '"session_id": "named-one"' in out
    assert "newest-one" not in out


def test_create_issue_sends_the_pinned_gh_call(project, repo, stub_host, monkeypatch, capsys):
    calls = []
    bodies = []

    def fake_run(argv, **kwargs):
        if argv[0] != "gh":
            return _Completed(1, "", "not gh")
        calls.append((list(argv), dict(kwargs)))
        bodies.append(Path(argv[argv.index("--body-file") + 1]).read_text(encoding="utf-8"))
        return _Completed(0, "https://github.com/example/lab/issues/99\n", "")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    assert cli.main(_build(project, repo, "--create")) == 0
    assert capsys.readouterr().out == "https://github.com/example/lab/issues/99\n"
    assert len(calls) == 1
    argv, kwargs = calls[0]
    assert argv[:5] == ["gh", "issue", "create", "--title", "Handover telemetry: repo"]
    assert argv[5] == "--body-file"
    assert argv[6].endswith(".md")
    assert argv[7:] == ["--label", "handover"]
    assert kwargs == {"capture_output": True, "text": True, "timeout": 120, "shell": False}
    assert bodies == [GOLDEN_MD]


def test_gh_failure_message_is_exact(project, repo, stub_host, monkeypatch, capsys):
    monkeypatch.setattr(
        cli.subprocess, "run", lambda *a, **k: _Completed(3, "", "boom line\n")
    )
    assert cli.main(_build(project, repo, "--create")) == 2
    assert capsys.readouterr().err == "handover_telemetry: gh failed: boom line\n"


def test_gh_missing_tool_message_is_exact(project, repo, stub_host, monkeypatch, capsys):
    def raise_os_error(*args, **kwargs):
        raise OSError("missing gh")

    monkeypatch.setattr(cli.subprocess, "run", raise_os_error)
    assert cli.main(_build(project, repo, "--create")) == 2
    assert capsys.readouterr().err == "handover_telemetry: gh failed: missing gh\n"


def test_gh_timeout_message_is_exact(project, repo, stub_host, monkeypatch, capsys):
    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="gh", timeout=120)

    monkeypatch.setattr(cli.subprocess, "run", raise_timeout)
    assert cli.main(_build(project, repo, "--create")) == 2
    assert capsys.readouterr().err == "handover_telemetry: gh failed: Command 'gh' timed out after 120 seconds\n"


def test_main_help_text_is_pinned(monkeypatch, capsys):
    monkeypatch.setenv("COLUMNS", "80")
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    assert capsys.readouterr().out == HELP_MAIN


def test_build_help_text_is_pinned(monkeypatch, capsys):
    monkeypatch.setenv("COLUMNS", "80")
    with pytest.raises(SystemExit) as exc:
        cli.main(["build", "--help"])
    assert exc.value.code == 0
    assert capsys.readouterr().out == HELP_BUILD


def test_sessions_help_text_is_pinned(monkeypatch, capsys):
    monkeypatch.setenv("COLUMNS", "80")
    with pytest.raises(SystemExit) as exc:
        cli.main(["sessions", "--help"])
    assert exc.value.code == 0
    assert capsys.readouterr().out == HELP_SESSIONS


def test_no_command_error_is_pinned(monkeypatch, capsys):
    monkeypatch.setenv("COLUMNS", "80")
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2
    assert capsys.readouterr().err == NO_COMMAND_ERROR


def test_build_without_repo_flag_uses_the_working_directory(
    project, repo, stub_host, monkeypatch, capsys
):
    monkeypatch.setattr(cli.Path, "cwd", classmethod(lambda cls: repo))
    code = cli.main(["build", "--project-dir", str(project), "--transcript", str(project / "main.jsonl")])
    assert code == 0
    assert capsys.readouterr().out == GOLDEN_MD


def test_record_model_names_sorts_and_skips_blanks(tmp_path):
    from handover_telemetry import transcript

    path = tmp_path / "two.jsonl"
    lines = [
        '{"type": "assistant", "sessionId": "s1", "timestamp": "2026-01-01T00:00:01Z",'
        ' "message": {"id": "m1", "model": "z-model", "usage": {}, "content": []}}',
        '{"type": "assistant", "sessionId": "s1", "timestamp": "2026-01-01T00:00:02Z",'
        ' "message": {"id": "m2", "model": "a-model", "usage": {}, "content": []}}',
        '{"type": "assistant", "sessionId": "s1", "timestamp": "2026-01-01T00:00:03Z",'
        ' "message": {"id": "m3", "usage": {}, "content": []}}',
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert cli.record_model_names(transcript.parse_session(path)) == ["a-model", "z-model"]


def test_build_passes_the_repo_to_the_machine_and_dora_reads(
    project, repo, monkeypatch, capsys
):
    import subprocess

    from handover_telemetry import machine

    (repo / "marker.txt").write_text("x", encoding="utf-8")

    def git(*args: str, date: str) -> None:
        env = dict(os.environ)
        env.update(
            {
                "GIT_AUTHOR_DATE": date,
                "GIT_COMMITTER_DATE": date,
                "GIT_AUTHOR_NAME": "T",
                "GIT_AUTHOR_EMAIL": "t@example.org",
                "GIT_COMMITTER_NAME": "T",
                "GIT_COMMITTER_EMAIL": "t@example.org",
            }
        )
        out = subprocess.run(
            ["git", *args], cwd=repo, env=env, capture_output=True, text=True, timeout=30
        )
        assert out.returncode == 0, out.stderr

    git("init", "-b", "main", date="2026-10-29T08:00:00 +0000")
    git("add", ".", date="2026-10-29T08:00:00 +0000")
    git("commit", "-m", "init", date="2026-10-29T08:00:00 +0000")
    git("checkout", "-b", "feat/x", date="2026-10-29T09:00:00 +0000")
    (repo / "x.txt").write_text("x", encoding="utf-8")
    git("add", ".", date="2026-10-29T09:00:00 +0000")
    git("commit", "-m", "work", date="2026-10-29T09:00:00 +0000")
    git("checkout", "main", date="2026-10-29T11:00:00 +0000")
    git("merge", "--no-ff", "-m", "feat: x (#1)", "feat/x", date="2026-10-29T11:00:00 +0000")

    seen = []
    real_disk = machine.disk_total_gb

    def spy_disk(repo_arg):
        seen.append(repo_arg)
        return real_disk(repo_arg)

    monkeypatch.setattr(machine, "disk_total_gb", spy_disk)
    assert cli.main(_build(project, repo)) == 0
    out = capsys.readouterr().out
    assert seen == [repo]
    assert "- change lead time: 3600000 ms" in out
