"""Tests for the ledger subcommand: identity, append formats, refusals,
and the default scratch directory."""

import json

from plan_exec.cli import main


def _plan(tmp_path, name="plan.md"):
    plan = tmp_path / name
    plan.write_text("# plan\n", encoding="utf-8")
    return plan


def test_init_creates_the_identity_line(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "init"]) == 0
    first = (out / "progress.md").read_text(encoding="utf-8").splitlines()[0]
    assert first == f"# plan_exec ledger - plan: {plan.resolve()}"


def test_init_is_idempotent_on_matching_identity(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    (out / "progress.md").write_text(
        f"# plan_exec ledger - plan: {plan.resolve()}\nTask 1: complete\n", encoding="utf-8"
    )
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "init"]) == 0
    assert "Task 1: complete" in (out / "progress.md").read_text(encoding="utf-8")


def test_init_refuses_a_foreign_identity(tmp_path):
    plan = _plan(tmp_path, "plan.md")
    other = _plan(tmp_path, "other.md")
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    assert main(["ledger", "--plan", str(other), "--dir", str(out), "init"]) == 2
    lines = (out / "progress.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1


def test_complete_appends_the_pinned_format(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    code = main(
        [
            "ledger", "--plan", str(plan), "--dir", str(out),
            "complete", "--task", "1.2", "--tests", "pytest -k task12", "--result", "3 passed",
        ]
    )
    assert code == 0
    lines = (out / "progress.md").read_text(encoding="utf-8").splitlines()
    assert lines[-1] == "Task 1.2: complete (tests: pytest -k task12 -> 3 passed)"
    assert lines[0].startswith("# plan_exec ledger")


def test_task_rule_appends_the_pinned_format(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    code = main(
        [
            "ledger", "--plan", str(plan), "--dir", str(out), "task-rule",
            "--task", "2.1", "--what", "split the parser", "--why", "complexity 14",
            "--cost", "a wrong split hides a bug",
        ]
    )
    assert code == 0
    lines = (out / "progress.md").read_text(encoding="utf-8").splitlines()
    assert lines[-1] == "Task 2.1: Ruling: split the parser - complexity 14 - a wrong split hides a bug"


def test_actions_on_a_missing_ledger_exit_two(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "complete", "--task", "1", "--tests", "t", "--result", "r"]) == 2
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "task-rule", "--task", "1", "--what", "w", "--why", "y", "--cost", "c"]) == 2
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "show"]) == 2


def test_actions_on_an_identityless_ledger_exit_two(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    out.mkdir()
    (out / "progress.md").write_text("loose lines\n", encoding="utf-8")
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "complete", "--task", "1", "--tests", "t", "--result", "r"]) == 2
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "show"]) == 2


def test_show_prints_the_ledger(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    main(["ledger", "--plan", str(plan), "--dir", str(out), "complete", "--task", "1", "--tests", "t", "--result", "r"])
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "show"]) == 0
    printed = capsys.readouterr().out
    assert "# plan_exec ledger" in printed
    assert "Task 1: complete" in printed


def test_show_json_reports_lines(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    code = main(["--json", "ledger", "--plan", str(plan), "--dir", str(out), "show"])
    assert code == 0
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["ok"] is True
    assert data["lines"][0].startswith("# plan_exec ledger")


def test_complete_requires_task_tests_and_result(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "complete"]) == 2


def test_task_rule_requires_all_parts(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "task-rule", "--task", "1", "--what", "w"]) == 2


def test_plan_resolves_relative_paths_before_compare(tmp_path, monkeypatch):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    monkeypatch.chdir(tmp_path)
    main(["ledger", "--plan", "plan.md", "--dir", str(out), "init"])
    assert main(["ledger", "--plan", str(plan.resolve()), "--dir", str(out), "init"]) == 0


def test_default_dir_sits_under_the_repo_root(tmp_path, monkeypatch):
    import subprocess

    root = tmp_path / "repo"
    (root / "sub").mkdir(parents=True)
    subprocess.run(["git", "-C", str(root), "init", "-q", "-b", "main"], check=True)
    plan = root / "plan.md"
    plan.write_text("# plan\n", encoding="utf-8")
    monkeypatch.chdir(root / "sub")
    assert main(["ledger", "--plan", str(plan), "init"]) == 0
    expected = root / ".plan_exec" / "plan.md" / "progress.md"
    assert expected.is_file()
    assert not (root / "sub" / ".plan_exec").exists()


def test_foreign_identity_message_names_both_plans(tmp_path, capsys):
    plan = _plan(tmp_path, "plan.md")
    other = _plan(tmp_path, "other.md")
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    code = main(["--json", "ledger", "--plan", str(other), "--dir", str(out), "init"])
    assert code == 2
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["ok"] is False
    assert "other.md" in data["error"] and "plan.md" in data["error"]


def test_missing_ledger_message_names_the_path(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    code = main(["--json", "ledger", "--plan", str(plan), "--dir", str(out), "show"])
    assert code == 2
    data = json.loads(capsys.readouterr().out)
    assert data["error"] == f"no ledger at {out / 'progress.md'}"


def test_identityless_ledger_message_says_so(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    out.mkdir()
    (out / "progress.md").write_text("loose\n", encoding="utf-8")
    code = main(["--json", "ledger", "--plan", str(plan), "--dir", str(out), "show"])
    assert code == 2
    data = json.loads(capsys.readouterr().out)
    assert data["error"] == f"ledger at {out / 'progress.md'} carries no identity line"


def test_default_dir_falls_back_to_cwd_outside_a_repo(tmp_path, monkeypatch):
    bare = tmp_path / "bare"
    bare.mkdir()
    plan = bare / "plan.md"
    plan.write_text("# plan\n", encoding="utf-8")
    monkeypatch.chdir(bare)
    assert main(["ledger", "--plan", "plan.md", "init"]) == 0
    assert (bare / ".plan_exec" / "plan.md" / "progress.md").is_file()


def test_init_creates_a_nested_dir(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "deep" / "led"
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "init"]) == 0
    assert (out / "progress.md").is_file()


def test_init_into_an_existing_empty_dir(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    out.mkdir()
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "init"]) == 0
    assert (out / "progress.md").is_file()


def test_json_init_reports_the_path(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    code = main(["--json", "ledger", "--plan", str(plan), "--dir", str(out), "init"])
    assert code == 0
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["path"] == str(out / "progress.md")


def test_json_complete_reports_the_path(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    code = main(
        [
            "--json", "ledger", "--plan", str(plan), "--dir", str(out),
            "complete", "--task", "1", "--tests", "t", "--result", "r",
        ]
    )
    assert code == 0
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["path"] == str(out / "progress.md")


def test_show_prints_the_file_content_exactly(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    main(["ledger", "--plan", str(plan), "--dir", str(out), "complete", "--task", "1", "--tests", "t", "--result", "r"])
    capsys.readouterr()
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "show"]) == 0
    assert capsys.readouterr().out == (out / "progress.md").read_text(encoding="utf-8")


def test_non_json_error_goes_to_stderr_with_prefix(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    code = main(["ledger", "--plan", str(plan), "--dir", str(out), "show"])
    assert code == 2
    captured = capsys.readouterr()
    assert captured.err == f"error: no ledger at {out / 'progress.md'}\n"
    assert captured.out == ""


def test_complete_missing_result_flag_exits_two(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    argv = [
        "ledger", "--plan", str(plan), "--dir", str(out),
        "complete", "--task", "1", "--tests", "t",
    ]
    assert main(argv) == 2


def test_complete_missing_tests_flag_exits_two(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    argv = [
        "ledger", "--plan", str(plan), "--dir", str(out),
        "complete", "--task", "1", "--result", "r",
    ]
    assert main(argv) == 2


def test_task_rule_missing_what_flag_exits_two(tmp_path):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    argv = [
        "ledger", "--plan", str(plan), "--dir", str(out), "task-rule",
        "--task", "1", "--why", "y", "--cost", "c",
    ]
    assert main(argv) == 2


def test_flag_error_messages_are_pinned(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    code = main(["--json", "ledger", "--plan", str(plan), "--dir", str(out), "complete"])
    assert code == 2
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["error"] == "complete needs --task, --tests, and --result"
    code = main(["--json", "ledger", "--plan", str(plan), "--dir", str(out), "task-rule"])
    assert code == 2
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["error"] == "task-rule needs --task, --what, --why, and --cost"


def test_json_task_rule_reports_the_path(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    code = main(
        [
            "--json", "ledger", "--plan", str(plan), "--dir", str(out), "task-rule",
            "--task", "2.1", "--what", "w", "--why", "y", "--cost", "c",
        ]
    )
    assert code == 0
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["path"] == str(out / "progress.md")


def test_non_json_init_prints_the_path_exactly(tmp_path, capsys):
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    assert main(["ledger", "--plan", str(plan), "--dir", str(out), "init"]) == 0
    assert capsys.readouterr().out == f"{out / 'progress.md'}\n"


def test_init_with_a_dir_that_is_a_file_exits_two(tmp_path, capsys):
    plan = _plan(tmp_path)
    blocker = tmp_path / "led"
    blocker.write_text("not a directory\n", encoding="utf-8")
    code = main(["--json", "ledger", "--plan", str(plan), "--dir", str(blocker), "init"])
    assert code == 2
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["error"].startswith("cannot write ledger")


def test_append_to_a_readonly_ledger_exits_two(tmp_path, capsys):
    import os
    import stat

    if os.geteuid() == 0:
        import pytest

        pytest.skip("root ignores file modes")
    plan = _plan(tmp_path)
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    path = out / "progress.md"
    path.chmod(stat.S_IRUSR)
    try:
        code = main(
            [
                "--json", "ledger", "--plan", str(plan), "--dir", str(out),
                "complete", "--task", "1", "--tests", "t", "--result", "r",
            ]
        )
    finally:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    assert code == 2
    data = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert data["error"].startswith("cannot write ledger")


def test_append_to_a_foreign_ledger_refuses(tmp_path, capsys):
    plan = _plan(tmp_path, "plan.md")
    other = _plan(tmp_path, "other.md")
    out = tmp_path / "led"
    main(["ledger", "--plan", str(plan), "--dir", str(out), "init"])
    code = main(
        [
            "--json", "ledger", "--plan", str(other), "--dir", str(out),
            "complete", "--task", "1", "--tests", "t", "--result", "r",
        ]
    )
    assert code == 2
    assert "belongs to" in json.loads(capsys.readouterr().out.splitlines()[-1])["error"]

