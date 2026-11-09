"""Tests for the named-session lookup: the cross-project search, the
top-level rule, the newest-match selection, the path-order tie, and
the CLI resolution paths that use them."""

import argparse
import os
from pathlib import Path

import pytest
from handover_telemetry import cli, transcript

FIXTURES = Path(__file__).parent / "fixtures"
SESSION_TXT = (FIXTURES / "session" / "main.jsonl").read_text(encoding="utf-8")
SESSION_ID = "abc-123"


@pytest.fixture()
def claude_root(tmp_path) -> Path:
    root = tmp_path / "claude-root"
    root.mkdir()
    return root


def _project_dir(root: Path, name: str) -> Path:
    project = root / name
    project.mkdir(parents=True)
    return project


def _put_session(project: Path, session_id: str = SESSION_ID) -> Path:
    named = project / f"{session_id}.jsonl"
    named.write_text(SESSION_TXT, encoding="utf-8")
    return named


def _set_mtime(path: Path, stamp: int) -> None:
    os.utime(path, (stamp, stamp))


def _patch_root(monkeypatch, root: Path) -> None:
    monkeypatch.setattr(transcript, "projects_root", lambda: root)


def test_find_named_transcript_finds_a_match_in_another_project_dir(
    monkeypatch, claude_root
):
    _project_dir(claude_root, "-home-repos-lab")
    other = _project_dir(claude_root, "-home-repos-lab-worktrees-demo")
    named = _put_session(other)
    _patch_root(monkeypatch, claude_root)
    assert transcript.find_named_transcript(SESSION_ID) == named


def test_find_named_transcript_ignores_sidechain_files(monkeypatch, claude_root):
    project = _project_dir(claude_root, "-home-repos-lab")
    sub = project / SESSION_ID / "subagents"
    sub.mkdir(parents=True)
    (sub / f"{SESSION_ID}.jsonl").write_text(SESSION_TXT, encoding="utf-8")
    _patch_root(monkeypatch, claude_root)
    assert transcript.find_named_transcript(SESSION_ID) is None


def test_find_named_transcript_prefers_the_newest_mtime(monkeypatch, claude_root):
    older = _put_session(_project_dir(claude_root, "-a-proj"))
    newer = _put_session(_project_dir(claude_root, "-b-proj"))
    _set_mtime(older, 1000)
    _set_mtime(newer, 2000)
    _patch_root(monkeypatch, claude_root)
    assert transcript.find_named_transcript(SESSION_ID) == newer


def test_find_named_transcript_breaks_a_tie_by_path_order(
    monkeypatch, claude_root
):
    first = _put_session(_project_dir(claude_root, "-a-proj"))
    second = _put_session(_project_dir(claude_root, "-b-proj"))
    _set_mtime(first, 1000)
    _set_mtime(second, 1000)
    _patch_root(monkeypatch, claude_root)
    assert transcript.find_named_transcript(SESSION_ID) == first


def test_find_named_transcript_tie_ignores_the_iteration_order(
    monkeypatch, claude_root
):
    late = _project_dir(claude_root, "-b-proj")
    early = _project_dir(claude_root, "-a-proj")
    first = _put_session(early)
    second = _put_session(late)
    _set_mtime(first, 1000)
    _set_mtime(second, 1000)

    class _FixedOrderRoot:
        def is_dir(self):
            return True

        def iterdir(self):
            return iter([late, early])

    monkeypatch.setattr(transcript, "projects_root", lambda: _FixedOrderRoot())
    assert transcript.find_named_transcript(SESSION_ID) == first


def test_find_named_transcript_missing_projects_root_is_none(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "absent"))
    assert transcript.find_named_transcript(SESSION_ID) is None


def test_find_named_transcript_skips_a_project_shaped_file(
    monkeypatch, claude_root
):
    (claude_root / "not-a-dir").write_text("x", encoding="utf-8")
    _patch_root(monkeypatch, claude_root)
    assert transcript.find_named_transcript(SESSION_ID) is None


def test_find_named_transcript_skips_a_candidate_that_loses_its_stat(
    monkeypatch, claude_root
):
    stable = _put_session(_project_dir(claude_root, "-a-proj"))
    _put_session(_project_dir(claude_root, "-b-proj"))
    real_mtime = transcript._mtime

    def _flaky_mtime(path):
        if "-b-proj" in str(path):
            raise OSError("file vanished")
        return real_mtime(path)

    monkeypatch.setattr(transcript, "_mtime", _flaky_mtime)
    _patch_root(monkeypatch, claude_root)
    assert transcript.find_named_transcript(SESSION_ID) == stable


def _args(**overrides) -> argparse.Namespace:
    base = {
        "transcript": None,
        "session": None,
        "project_dir": None,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_resolution_transcript_flag_wins_and_no_search_runs(
    monkeypatch, tmp_path
):
    direct = tmp_path / "direct.jsonl"
    _patch_root(monkeypatch, tmp_path / "absent-root")
    assert cli._resolve_transcript(_args(transcript=direct), tmp_path) == (
        direct
    )


def test_resolution_launch_slug_hit_beats_a_newer_remote_match(
    monkeypatch, tmp_path
):
    launch = tmp_path / "launch-proj"
    launch.mkdir()
    local = _put_session(launch)
    _set_mtime(local, 1000)
    remote_parent = tmp_path / "root"
    remote = _put_session(_project_dir(remote_parent, "-other-proj"))
    _set_mtime(remote, 2000)
    _patch_root(monkeypatch, remote_parent)
    assert cli._resolve_transcript(_args(session=SESSION_ID), launch) == local


def test_resolution_cross_project_search_runs_on_a_launch_miss(
    monkeypatch, tmp_path
):
    launch = tmp_path / "launch-proj"
    launch.mkdir()
    remote = _put_session(_project_dir(tmp_path, "-other-proj"))
    _patch_root(monkeypatch, tmp_path)
    assert cli._resolve_transcript(_args(session=SESSION_ID), launch) == remote


def test_resolution_pinned_project_dir_sets_the_scope(monkeypatch, tmp_path):
    pinned = tmp_path / "pinned-proj"
    pinned.mkdir()
    named = _put_session(pinned)
    _patch_root(monkeypatch, tmp_path / "absent-root")
    got = cli._resolve_transcript(
        _args(session=SESSION_ID, project_dir=pinned), pinned
    )
    assert got == named


def test_resolution_pinned_miss_does_not_search_other_dirs(
    monkeypatch, tmp_path
):
    pinned = tmp_path / "pinned-proj"
    pinned.mkdir()
    _put_session(_project_dir(tmp_path, "-other-proj"))
    _patch_root(monkeypatch, tmp_path)
    got = cli._resolve_transcript(
        _args(session=SESSION_ID, project_dir=pinned), pinned
    )
    assert got is None


def test_resolution_named_miss_returns_none(monkeypatch, tmp_path):
    _patch_root(monkeypatch, tmp_path)
    assert cli._resolve_transcript(_args(session="ghost"), tmp_path) is None


def test_resolution_default_keeps_the_newest_transcript(tmp_path):
    newest = _put_session(tmp_path, "def-456")
    older = _put_session(tmp_path, "abc-123")
    _set_mtime(newest, 2000)
    _set_mtime(older, 1000)
    assert cli._resolve_transcript(_args(), tmp_path) == newest


def test_build_finds_a_named_session_in_another_project_dir(
    tmp_path, monkeypatch, capsys
):
    repo = tmp_path / "repo"
    repo.mkdir()
    root = tmp_path / "claude-root"
    root.mkdir()
    other = _project_dir(root, "-home-repos-lab-worktrees-demo")
    _put_session(other)
    launch = tmp_path / "launch"
    launch.mkdir()
    _patch_root(monkeypatch, root)
    monkeypatch.chdir(launch)
    code = cli.main(["build", "--session", SESSION_ID, "--repo", str(repo)])
    assert code == 0
    assert "## Telemetry" in capsys.readouterr().out


def test_build_pinned_miss_exits_2_and_names_the_session(
    tmp_path, monkeypatch, capsys
):
    repo = tmp_path / "repo"
    repo.mkdir()
    launch = tmp_path / "launch"
    launch.mkdir()
    _put_session(launch)
    pinned = tmp_path / "pinned"
    pinned.mkdir()
    root = tmp_path / "claude-root"
    root.mkdir()
    _patch_root(monkeypatch, root)
    code = cli.main(
        [
            "build",
            "--session",
            SESSION_ID,
            "--project-dir",
            str(pinned),
            "--repo",
            str(repo),
        ]
    )
    assert code == 2
    assert f"no transcript for session {SESSION_ID}" in (
        capsys.readouterr().err
    )


def test_build_global_miss_exits_2_and_names_the_session(
    tmp_path, monkeypatch, capsys
):
    repo = tmp_path / "repo"
    repo.mkdir()
    root = tmp_path / "claude-root"
    root.mkdir()
    _patch_root(monkeypatch, root)
    code = cli.main(["build", "--session", "ghost-1", "--repo", str(repo)])
    assert code == 2
    assert "no transcript for session ghost-1" in capsys.readouterr().err


def test_build_named_miss_keeps_no_newest_fallback(
    tmp_path, monkeypatch, capsys
):
    repo = tmp_path / "repo"
    repo.mkdir()
    root = tmp_path / "claude-root"
    root.mkdir()
    launch = tmp_path / "launch"
    launch.mkdir()
    slug_dir = root / transcript.project_dir_for(launch).name
    slug_dir.mkdir(parents=True)
    _put_session(slug_dir, "real-999")
    _patch_root(monkeypatch, root)
    monkeypatch.chdir(launch)
    code = cli.main(["build", "--session", "ghost-1", "--repo", str(repo)])
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "no transcript for session ghost-1" in captured.err


def test_build_transcript_flag_miss_names_the_path(
    tmp_path, monkeypatch, capsys
):
    repo = tmp_path / "repo"
    repo.mkdir()
    gone = tmp_path / "gone.jsonl"
    root = tmp_path / "claude-root"
    root.mkdir()
    _patch_root(monkeypatch, root)
    code = cli.main(
        [
            "build",
            "--transcript",
            str(gone),
            "--session",
            SESSION_ID,
            "--repo",
            str(repo),
        ]
    )
    assert code == 2
    assert f"no transcript at {gone}" in capsys.readouterr().err


def test_build_without_a_session_flag_reports_the_directory(
    tmp_path, monkeypatch, capsys
):
    repo = tmp_path / "repo"
    repo.mkdir()
    empty = tmp_path / "empty-project"
    empty.mkdir()
    root = tmp_path / "claude-root"
    root.mkdir()
    _patch_root(monkeypatch, root)
    code = cli.main(
        [
            "build",
            "--project-dir",
            str(empty),
            "--repo",
            str(repo),
        ]
    )
    assert code == 2
    assert f"no transcript at {empty}" in capsys.readouterr().err
