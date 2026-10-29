"""Owned gate tests for the --fail-above flag.

This repository's copy of dryer adds --fail-above so a gate run can fail on
reported candidates. Upstream dryer exits 0 on findings; these tests pin the
added behavior and prove the default behavior is unchanged.
"""

from pathlib import Path

from dryer.cli import parse_args, run


def write_source(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


LEFT = "def alpha(xs):\n    ys = filter(xs, odd)\n    zs = map(ys, inc)\n    return list(zs)\n"
RIGHT = "def beta(items):\n    kept = filter(items, even)\n    out = map(kept, dec)\n    return list(out)\n"


def write_pair(root: Path) -> None:
    write_source(root, "src/left.py", LEFT)
    write_source(root, "src/right.py", RIGHT)


def test_fail_above_parses():
    options = parse_args(["--fail-above", "src"])
    assert options.fail_above is True
    assert parse_args(["src"]).fail_above is False


def test_fail_above_exits_2_on_candidates(tmp_path, capsys):
    write_pair(tmp_path)
    code = run(["--root", str(tmp_path), "--min-lines", "3", "--min-nodes", "1", "--fail-above"])
    out = capsys.readouterr().out
    assert code == 2
    assert "DUPLICATE score=1.00" in out
    assert (tmp_path / ".metrics" / "dry.edn").is_file()


def test_default_still_exits_0_on_candidates(tmp_path, capsys):
    write_pair(tmp_path)
    code = run(["--root", str(tmp_path), "--min-lines", "3", "--min-nodes", "1"])
    assert code == 0
    assert "DUPLICATE score=1.00" in capsys.readouterr().out


def test_fail_above_exits_0_on_a_clean_tree(tmp_path, capsys):
    write_source(tmp_path, "src/one.py", LEFT)
    code = run(["--root", str(tmp_path), "--min-lines", "3", "--min-nodes", "1", "--fail-above"])
    assert code == 0
    assert "DUPLICATE" not in capsys.readouterr().out
