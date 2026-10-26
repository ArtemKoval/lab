"""Pin the CLI surface: help text, option names, and action choices.
Assertions anchor to line boundaries because a mutation that wraps a
string literal must not still match a substring check."""

import re

import pytest
from plan_exec.cli import _build_parser

MAIN_DESCRIPTION = "Task briefs, review packages, and execution ledgers for plan runs."
SUBCOMMANDS = (
    ("brief", "extract one task as a brief"),
    ("package", "package a commit range for review"),
    ("ledger", "append-only execution ledger"),
)
OPTION_HELP = {
    "brief": (
        ("--plan",),
        ("--task",),
        ("--out",),
    ),
    "package": (
        ("--repo",),
        ("--base",),
        ("--head",),
        ("--out",),
    ),
    "ledger": (
        ("--plan",),
        ("--dir",),
        ("--task",),
        ("--tests",),
        ("--result",),
        ("--what",),
        ("--why",),
        ("--cost",),
    ),
}


def _capture_help(capsys, argv):
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(argv)
    assert excinfo.value.code == 0
    return capsys.readouterr().out


def _assert_line(out, pattern):
    assert re.search(pattern, out, re.MULTILINE), pattern


def test_main_help_names_the_program_and_description(capsys):
    out = _capture_help(capsys, ["--help"])
    _assert_line(out, r"^usage: plan_exec\b")
    _assert_line(out, rf"^{re.escape(MAIN_DESCRIPTION)}\s*$")
    _assert_line(out, r"--json\s+print machine-readable output\s*$")


def test_main_help_lists_each_subcommand_with_its_help(capsys):
    out = _capture_help(capsys, ["--help"])
    for name, text in SUBCOMMANDS:
        _assert_line(out, rf"{name}\s+{re.escape(text)}\s*$")


def test_every_option_help_line_matches(capsys):
    for sub, options in OPTION_HELP.items():
        out = _capture_help(capsys, [sub, "--help"])
        for flag, in options:
            _assert_line(out, rf"{flag}\s+\S.*\s*$")


def test_ledger_help_lists_the_action_choices(capsys):
    out = _capture_help(capsys, ["ledger", "--help"])
    _assert_line(out, r"\{init,complete,task-rule,show\}")


def test_brief_requires_all_three_options():
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(["brief"])
    assert excinfo.value.code == 2


def test_package_base_is_required_and_head_defaults():
    args = _build_parser().parse_args(["package", "--repo", "r", "--base", "x", "--out", "o"])
    assert args.head == "HEAD"
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(["package", "--repo", "r", "--out", "o"])
    assert excinfo.value.code == 2


def test_ledger_rejects_unknown_actions():
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(["ledger", "--plan", "p", "explode"])
    assert excinfo.value.code == 2


def test_json_is_a_global_flag_before_the_subcommand():
    args = _build_parser().parse_args(["--json", "brief", "--plan", "p", "--task", "1", "--out", "o"])
    assert args.json is True
    args = _build_parser().parse_args(["brief", "--plan", "p", "--task", "1", "--out", "o"])
    assert args.json is False


def test_no_subcommand_is_an_error():
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args([])
    assert excinfo.value.code == 2


@pytest.mark.parametrize(
    "argv",
    [
        ["brief", "--task", "1", "--out", "o"],
        ["brief", "--plan", "p", "--out", "o"],
        ["brief", "--plan", "p", "--task", "1"],
        ["package", "--base", "x", "--out", "o"],
        ["package", "--repo", "r", "--out", "o"],
        ["package", "--repo", "r", "--base", "x"],
        ["ledger", "--dir", "d", "init"],
    ],
)
def test_every_required_option_is_required(argv):
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(argv)
    assert excinfo.value.code == 2


def test_path_typed_options_parse_to_path_objects():
    args = _build_parser().parse_args(
        ["brief", "--plan", "p", "--task", "1", "--out", "o"]
    )
    import pathlib

    assert isinstance(args.plan, pathlib.Path)
    assert isinstance(args.out, pathlib.Path)
    args = _build_parser().parse_args(
        ["package", "--repo", "r", "--base", "x", "--out", "o"]
    )
    assert isinstance(args.repo, pathlib.Path)
    assert isinstance(args.out, pathlib.Path)
    args = _build_parser().parse_args(
        ["ledger", "--plan", "p", "--dir", "d", "show"]
    )
    assert isinstance(args.plan, pathlib.Path)
    assert isinstance(args.out_dir, pathlib.Path)
    args = _build_parser().parse_args(["ledger", "--plan", "p", "show"])
    assert args.out_dir is None


def test_json_after_the_subcommand_is_rejected():
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(["brief", "--json", "--plan", "p", "--task", "1", "--out", "o"])
    assert excinfo.value.code == 2


def test_abbreviated_flags_are_rejected():
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(["--js", "brief", "--plan", "p", "--task", "1", "--out", "o"])
    assert excinfo.value.code == 2
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(["brief", "--ta", "1", "--plan", "p", "--out", "o"])
    assert excinfo.value.code == 2


def test_abbreviations_rejected_on_every_subparser():
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(["package", "--ba", "x", "--repo", "r", "--out", "o"])
    assert excinfo.value.code == 2
    with pytest.raises(SystemExit) as excinfo:
        _build_parser().parse_args(["ledger", "--pla", "p", "init"])
    assert excinfo.value.code == 2
