"""Tests for the CLI surface: the build and sessions subcommands, the
flags, the exit codes, and the flag-gated gh path with a fake gh."""

import json as jsonlib
import os
import stat
from pathlib import Path

import pytest

from handover_telemetry import cli

FIXTURES = Path(__file__).parent / "fixtures"
SESSION_DIR = FIXTURES / "session"


@pytest.fixture()
def project(tmp_path) -> Path:
    main = tmp_path / "main.jsonl"
    main.write_text((SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    sub = tmp_path / "sess-1" / "subagents"
    sub.mkdir(parents=True)
    (sub / "agent-42.jsonl").write_text(
        (SESSION_DIR / "sess-1" / "subagents" / "agent-42.jsonl").read_text(
            encoding="utf-8"
        ),
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def repo(tmp_path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".cc_logging").mkdir()
    return repo


def _fake_gh(tmp_path, fail=False) -> Path:
    marker = tmp_path / "gh-calls.log"
    body = (
        "#!/bin/sh\n"
        f'echo "$@" >> {marker}\n'
        + ("exit 1\n" if fail else "echo https://github.com/example/lab/issues/99\n")
    )
    gh_dir = tmp_path / "fakebin"
    gh_dir.mkdir(exist_ok=True)
    gh = gh_dir / "gh"
    gh.write_text(body, encoding="utf-8")
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    return gh_dir


def test_build_writes_markdown_to_stdout(project, repo, capsys):
    code = cli.main(
        ["build", "--project-dir", str(project), "--transcript", str(project / "main.jsonl"), "--repo", str(repo)]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "## Telemetry" in out
    assert "### Funnel" in out


def test_build_gives_sidechain_calls_a_derived_duration(project, repo, capsys):
    code = cli.main(
        ["build", "--project-dir", str(project), "--transcript", str(project / "main.jsonl"), "--repo", str(repo)]
    )
    out = capsys.readouterr().out
    assert code == 0
    row = next(line for line in out.splitlines() if "agent-42 | Read" in line)
    assert "| 500 |" in row


def test_build_json_output_is_valid_json(project, repo, capsys):
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(project),
            "--transcript",
            str(project / "main.jsonl"),
            "--repo",
            str(repo),
            "--json",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    data = jsonlib.loads(out)
    assert data["fingerprint"]["session_id"] == "sess-1"


def test_build_writes_out_file(project, repo, tmp_path):
    target = tmp_path / "handover-report.md"
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(project),
            "--transcript",
            str(project / "main.jsonl"),
            "--repo",
            str(repo),
            "--out",
            str(target),
        ]
    )
    assert code == 0
    assert "## Telemetry" in target.read_text(encoding="utf-8")


def test_build_defaults_to_newest_transcript(project, repo, capsys):
    code = cli.main(["build", "--project-dir", str(project), "--repo", str(repo)])
    assert code == 0
    assert "## Telemetry" in capsys.readouterr().out


def test_build_session_flag_selects_by_session_id(project, repo, capsys):
    code = cli.main(["build", "--project-dir", str(project), "--session", "main", "--repo", str(repo)])
    assert code == 0
    assert "sess-1" in capsys.readouterr().out


def test_build_missing_transcript_exits_2(tmp_path, repo, capsys):
    code = cli.main(
        ["build", "--project-dir", str(tmp_path), "--transcript", str(tmp_path / "none.jsonl"), "--repo", str(repo)]
    )
    err = capsys.readouterr().err
    assert code == 2
    assert "none.jsonl" in err


def test_build_survives_a_null_questions_argument(tmp_path, repo, capsys):
    lines = [
        '{"type": "assistant", "sessionId": "s1", "requestId": "r1", "timestamp": "2026-01-01T00:00:01Z",'
        ' "message": {"id": "m1", "model": "m", "usage": {}, "content": ['
        '{"type": "tool_use", "id": "t1", "name": "AskUserQuestion", "input": {"questions": null}}]}}',
    ]
    path = tmp_path / "nullq.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    code = cli.main(
        ["build", "--project-dir", str(tmp_path), "--transcript", str(path), "--repo", str(repo)]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "via AskUserQuestion: -" in out


def test_build_empty_project_exits_2(tmp_path, repo):
    code = cli.main(["build", "--project-dir", str(tmp_path), "--repo", str(repo)])
    assert code == 2


def test_build_bad_prices_file_exits_2(project, repo, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(project),
            "--transcript",
            str(project / "main.jsonl"),
            "--repo",
            str(repo),
            "--prices",
            str(bad),
        ]
    )
    assert code == 2


def test_sessions_lists_sessions(project, capsys):
    code = cli.main(["sessions", "--project-dir", str(project)])
    out = capsys.readouterr().out
    assert code == 0
    assert "main.jsonl" in out
    assert "glm-5.3-flash" in out


def test_sessions_missing_dir_exits_2(tmp_path):
    assert cli.main(["sessions", "--project-dir", str(tmp_path / "none")]) == 2


def test_build_without_create_runs_no_gh(project, repo, tmp_path, monkeypatch, capsys):
    gh_dir = _fake_gh(tmp_path, fail=True)
    monkeypatch.setenv("PATH", f"{gh_dir}:{os.environ['PATH']}")
    code = cli.main(
        ["build", "--project-dir", str(project), "--transcript", str(project / "main.jsonl"), "--repo", str(repo)]
    )
    assert code == 0
    assert not (tmp_path / "gh-calls.log").exists()


def test_build_create_opens_the_issue(project, repo, tmp_path, monkeypatch, capsys):
    gh_dir = _fake_gh(tmp_path)
    monkeypatch.setenv("PATH", f"{gh_dir}:{os.environ['PATH']}")
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(project),
            "--transcript",
            str(project / "main.jsonl"),
            "--repo",
            str(repo),
            "--create",
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "issues/99" in out
    calls = (tmp_path / "gh-calls.log").read_text(encoding="utf-8")
    assert "issue" in calls and "create" in calls
    assert "--body-file" in calls


def test_create_deletes_the_body_file(project, repo, tmp_path, monkeypatch):
    gh_dir = _fake_gh(tmp_path)
    monkeypatch.setenv("PATH", f"{gh_dir}:{os.environ['PATH']}")
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(project),
            "--transcript",
            str(project / "main.jsonl"),
            "--repo",
            str(repo),
            "--create",
        ]
    )
    assert code == 0
    calls = (tmp_path / "gh-calls.log").read_text(encoding="utf-8")
    fields = calls.split()
    body = Path(fields[fields.index("--body-file") + 1])
    assert not body.exists()


def test_create_cleanup_survives_a_consumed_body_file(
    project, repo, tmp_path, monkeypatch
):
    marker = tmp_path / "gh-calls.log"
    gh_dir = tmp_path / "fakebin2"
    gh_dir.mkdir(exist_ok=True)
    gh = gh_dir / "gh"
    gh.write_text(
        "#!/bin/sh\n"
        f'echo "$@" >> {marker}\n'
        'rm -f "$6"\n'
        "echo https://github.com/example/lab/issues/99\n",
        encoding="utf-8",
    )
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{gh_dir}:{os.environ['PATH']}")
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(project),
            "--transcript",
            str(project / "main.jsonl"),
            "--repo",
            str(repo),
            "--create",
        ]
    )
    assert code == 0
    assert "--body-file" in marker.read_text(encoding="utf-8")


def test_build_create_failure_exits_2(project, repo, tmp_path, monkeypatch):
    gh_dir = _fake_gh(tmp_path, fail=True)
    monkeypatch.setenv("PATH", f"{gh_dir}:{os.environ['PATH']}")
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(project),
            "--transcript",
            str(project / "main.jsonl"),
            "--repo",
            str(repo),
            "--create",
        ]
    )
    assert code == 2


def test_no_command_exits_2(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2


def test_session_fallthrough_uses_newest(project, repo, capsys):
    code = cli.main(["build", "--project-dir", str(project), "--session", "absent", "--repo", str(repo)])
    assert code == 0
    assert "## Telemetry" in capsys.readouterr().out


def test_create_with_gh_missing_exits_2(project, repo, tmp_path, monkeypatch):
    empty_bin = tmp_path / "emptybin"
    empty_bin.mkdir()
    monkeypatch.setenv("PATH", str(empty_bin))
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(project),
            "--transcript",
            str(project / "main.jsonl"),
            "--repo",
            str(repo),
            "--create",
        ]
    )
    assert code == 2


def test_build_defaults_project_dir_to_cwd(project, repo, monkeypatch, tmp_path, capsys):
    from handover_telemetry import transcript

    root = tmp_path / "claude-root"
    slug = transcript.project_dir_for(project)
    target = root / slug.name
    target.mkdir(parents=True)
    (target / "main.jsonl").write_text(
        (SESSION_DIR / "main.jsonl").read_text(encoding="utf-8"), encoding="utf-8"
    )
    monkeypatch.setattr(transcript, "projects_root", lambda: root)
    monkeypatch.chdir(project)
    code = cli.main(["build", "--repo", str(repo)])
    assert code == 0
    assert "## Telemetry" in capsys.readouterr().out
