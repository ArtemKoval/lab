"""Tests for the package subcommand: hermetic local git repositories
with an explicit commit identity (CI runners have none). Assertions pin
section shapes and exact messages so mutated format strings cannot hide."""

import json
import subprocess
from pathlib import Path

import pytest

from plan_exec.cli import main

GIT_IDENTITY = ["-c", "user.email=plan-exec@example.test", "-c", "user.name=plan-exec"]


def _git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), *GIT_IDENTITY, *args],
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path):
    """A git repo with two commits on different files."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    _git(root, "add", "a.txt")
    _git(root, "commit", "-q", "-m", "first commit")
    first = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    (root / "b.txt").write_text("two\n", encoding="utf-8")
    _git(root, "add", "b.txt")
    _git(root, "commit", "-q", "-m", "second commit")
    second = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return root, first, second


def test_package_writes_one_deterministic_file(repo, tmp_path):
    root, first, second = repo
    out = tmp_path / "out"
    assert main(["package", "--repo", str(root), "--base", first, "--head", second, "--out", str(out)]) == 0
    target = out / f"review-package-{first[:7]}-{second[:7]}.md"
    text = target.read_text(encoding="utf-8")
    assert text.startswith(f"# Review package {first[:7]}..{second[:7]}\n")
    assert "\n## Commits\n\n```\n" in text
    assert "\n## Stat\n\n```\n" in text
    assert "\n## Diff\n\n```diff\n" in text
    assert text.rstrip().endswith("```")
    assert "second commit" in text
    assert "b.txt" in text
    assert "first commit" not in text.split("## Commits")[1].split("## Stat")[0]


def test_package_leaves_repo_untouched(repo, tmp_path):
    root, first, second = repo
    out = tmp_path / "out"
    before = sorted(p.name for p in root.iterdir())
    main(["package", "--repo", str(root), "--base", first, "--head", second, "--out", str(out)])
    after = sorted(p.name for p in root.iterdir())
    assert before == after


def test_package_creates_the_out_directory(repo, tmp_path):
    root, first, second = repo
    out = tmp_path / "deep" / "out"
    assert main(["package", "--repo", str(root), "--base", first, "--head", second, "--out", str(out)]) == 0
    assert list(out.iterdir())


def test_package_twice_into_the_same_out_dir(repo, tmp_path):
    root, first, second = repo
    out = tmp_path / "out"
    argv = ["package", "--repo", str(root), "--base", first, "--head", second, "--out", str(out)]
    assert main(argv) == 0
    assert main(argv) == 0
    assert len(list(out.iterdir())) == 1


def test_equal_base_and_head_exits_two(repo, tmp_path, capsys):
    root, first, _ = repo
    out = tmp_path / "out"
    code = main(["--json", "package", "--repo", str(root), "--base", first, "--head", first, "--out", str(out)])
    assert code == 2
    data = json.loads(capsys.readouterr().out)
    assert "same commit" in data["error"]


def test_same_commit_message_pins_the_short_sha(repo, tmp_path, capsys):
    root, first, _ = repo
    out = tmp_path / "out"
    code = main(["--json", "package", "--repo", str(root), "--base", first, "--head", first, "--out", str(out)])
    assert code == 2
    data = json.loads(capsys.readouterr().out)
    assert data["error"] == f"base and head resolve to the same commit {first[:7]}"


def test_unknown_revision_exits_two(repo, tmp_path):
    root, _, second = repo
    out = tmp_path / "out"
    assert main(["package", "--repo", str(root), "--base", "nosuchref", "--head", second, "--out", str(out)]) == 2


def test_unknown_revision_error_carries_the_git_verbatim(repo, tmp_path, capsys):
    root, _, second = repo
    out = tmp_path / "out"
    code = main(["--json", "package", "--repo", str(root), "--base", "nosuchref", "--head", second, "--out", str(out)])
    assert code == 2
    data = json.loads(capsys.readouterr().out)
    assert "git rev-parse" in data["error"]
    assert "^{commit}" in data["error"]


def test_not_a_repo_exits_two(tmp_path):
    bare = tmp_path / "bare"
    bare.mkdir()
    out = tmp_path / "out"
    assert main(["package", "--repo", str(bare), "--base", "main", "--head", "HEAD", "--out", str(out)]) == 2


def test_head_defaults_to_head(repo, tmp_path):
    root, first, second = repo
    out = tmp_path / "out"
    assert main(["package", "--repo", str(root), "--base", first, "--out", str(out)]) == 0
    assert (out / f"review-package-{first[:7]}-{second[:7]}.md").is_file()


def test_json_output_reports_the_path(repo, tmp_path, capsys):
    root, first, second = repo
    out = tmp_path / "out"
    code = main(
        ["--json", "package", "--repo", str(root), "--base", first, "--head", second, "--out", str(out)]
    )
    assert code == 0
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["ok"] is True
    assert Path(data["path"]).is_file()


def test_commits_section_holds_oneline_entries_only(repo, tmp_path):
    root, first, second = repo
    out = tmp_path / "out"
    main(["package", "--repo", str(root), "--base", first, "--head", second, "--out", str(out)])
    text = next(out.iterdir()).read_text(encoding="utf-8")
    commits = text.split("## Commits")[1].split("## Stat")[0]
    assert "Author:" not in commits
    assert "second commit" in commits


def test_stat_section_holds_no_diff_lines(repo, tmp_path):
    root, first, second = repo
    out = tmp_path / "out"
    main(["package", "--repo", str(root), "--base", first, "--head", second, "--out", str(out)])
    text = next(out.iterdir()).read_text(encoding="utf-8")
    stat = text.split("## Stat")[1].split("## Diff")[0]
    assert "diff --git" not in stat
    assert "+++" not in stat
    assert "b.txt" in stat


def test_wide_context_merges_distant_hunks(tmp_path):
    """A 12-line file edited at both edges: -U10 merges the hunks into
    one; a dropped or narrowed -U10 splits them."""
    root = tmp_path / "repo12"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    lines = [f"line {n}" for n in range(1, 13)]
    (root / "big.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _git(root, "add", "big.txt")
    _git(root, "commit", "-q", "-m", "write big")
    base = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    lines[0] = "line 1 changed"
    lines[11] = "line 12 changed"
    (root / "big.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _git(root, "add", "big.txt")
    _git(root, "commit", "-q", "-m", "edit edges")
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    out = tmp_path / "out"
    assert main(["package", "--repo", str(root), "--base", base, "--head", head, "--out", str(out)]) == 0
    diff = next(out.iterdir()).read_text(encoding="utf-8").split("## Diff")[1]
    headers = [line for line in diff.splitlines() if line.startswith("@@ ")]
    assert len(headers) == 1
    assert "line 1 changed" in diff and "line 12 changed" in diff
