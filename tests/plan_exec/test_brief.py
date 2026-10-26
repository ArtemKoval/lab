"""Tests for the brief subcommand: both plan shapes, dotted ids, exact
brief content, and the failure contract. Content assertions compare the
whole brief so a mutated format string cannot still match."""

import json
from pathlib import Path

import pytest
from plan_exec import brief
from plan_exec.cli import main

SECTION_PLAN = """# Plan

## Intro

Some preamble that belongs to no task.

### Task 1: First

Do the first thing.

```python
print("step")
```

### Task 2: Second

Do the second thing.

### Notes

Later notes, not part of task 2.
"""

CHECKBOX_PLAN = """# Tasks

## 1. Group one

- [ ] 1.1 First task
  Body line one.
  Body line two.
  - [ ] nested deeper checkbox stays in the body

- [ ] 1.10 Second task
  Only line.

## 2. Group two

- [ ] 2.3 Dotted task
  The body.

  More body.

Trailing prose at column zero.
"""

SECTION_1_EXPECTED = (
    "### Task 1: First\n"
    "\n"
    "Do the first thing.\n"
    "\n"
    "```python\n"
    'print("step")\n'
    "```\n"
)
SECTION_2_EXPECTED = "### Task 2: Second\n\nDo the second thing.\n"
CHECKBOX_1_1_EXPECTED = (
    "- [ ] 1.1 First task\n"
    "  Body line one.\n"
    "  Body line two.\n"
    "  - [ ] nested deeper checkbox stays in the body\n"
)
CHECKBOX_2_3_EXPECTED = "- [ ] 2.3 Dotted task\n  The body.\n\n  More body.\n"


def _brief(tmp_path, plan_text, task_id):
    plan = tmp_path / "plan.md"
    plan.write_text(plan_text, encoding="utf-8")
    out = tmp_path / "out"
    code = main(["brief", "--plan", str(plan), "--task", task_id, "--out", str(out)])
    return code, out


def test_section_task_extracts_the_exact_body(tmp_path):
    code, out = _brief(tmp_path, SECTION_PLAN, "1")
    assert code == 0
    text = (out / "task-1-brief.md").read_text(encoding="utf-8")
    assert text == SECTION_1_EXPECTED


def test_section_task_stops_at_the_next_heading(tmp_path):
    code, out = _brief(tmp_path, SECTION_PLAN, "2")
    assert code == 0
    text = (out / "task-2-brief.md").read_text(encoding="utf-8")
    assert text == SECTION_2_EXPECTED


def test_section_task_preamble_stays_out(tmp_path):
    code, out = _brief(tmp_path, SECTION_PLAN, "1")
    assert code == 0
    assert "Some preamble" not in (out / "task-1-brief.md").read_text(encoding="utf-8")


def test_checkbox_task_extracts_the_exact_body(tmp_path):
    code, out = _brief(tmp_path, CHECKBOX_PLAN, "1.1")
    assert code == 0
    text = (out / "task-1.1-brief.md").read_text(encoding="utf-8")
    assert text == CHECKBOX_1_1_EXPECTED


def test_checkbox_task_stops_at_the_sibling(tmp_path):
    code, out = _brief(tmp_path, CHECKBOX_PLAN, "2.3")
    assert code == 0
    text = (out / "task-2.3-brief.md").read_text(encoding="utf-8")
    assert text == CHECKBOX_2_3_EXPECTED


def test_zero_padded_ids_normalize(tmp_path):
    code, out = _brief(tmp_path, CHECKBOX_PLAN, "01.10")
    assert code == 0
    text = (out / "task-1.10-brief.md").read_text(encoding="utf-8")
    assert text == "- [ ] 1.10 Second task\n  Only line.\n"


def test_section_task_id_zero_padded_matches_plain():
    assert brief.find_task(SECTION_PLAN, "02") == brief.find_task(SECTION_PLAN, "2")


def test_dotted_selector_skips_section_lines():
    with pytest.raises(brief.TaskNotFound) as excinfo:
        brief.find_task(SECTION_PLAN, "2.3")
    assert str(excinfo.value) == "no task '2.3' in plan"


def test_section_task_with_no_body_lines(tmp_path):
    code, out = _brief(tmp_path, "### Task 3: Last\n", "3")
    assert code == 0
    assert (out / "task-3-brief.md").read_text(encoding="utf-8") == "### Task 3: Last\n"


def test_checkbox_task_at_end_of_file(tmp_path):
    code, out = _brief(tmp_path, "- [ ] 5.1 Last task\n", "5.1")
    assert code == 0
    assert (out / "task-5.1-brief.md").read_text(encoding="utf-8") == "- [ ] 5.1 Last task\n"


def test_unknown_task_exits_two_without_output(tmp_path):
    code, out = _brief(tmp_path, CHECKBOX_PLAN, "9.9")
    assert code == 2
    assert not out.exists()


def test_non_numeric_task_exits_two_with_the_message(tmp_path):
    plan = tmp_path / "tasks.md"
    plan.write_text(CHECKBOX_PLAN, encoding="utf-8")
    out = tmp_path / "out"
    code = main(["brief", "--plan", str(plan), "--task", "one", "--out", str(out)])
    assert code == 2
    assert not out.exists()


def test_missing_plan_exits_two(tmp_path):
    out = tmp_path / "out"
    missing = tmp_path / "nope.md"
    code = main(["brief", "--plan", str(missing), "--task", "1", "--out", str(out)])
    assert code == 2
    assert not out.exists()


def test_json_output_reports_the_path(tmp_path, capsys):
    code, out = _brief(tmp_path, CHECKBOX_PLAN, "1.1")
    code = main(
        ["--json", "brief", "--plan", str(tmp_path / "plan.md"), "--task", "1.1", "--out", str(out)]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert payload["ok"] is True
    assert Path(payload["path"]).is_file()


def test_json_error_output_reports_ok_false(tmp_path, capsys):
    code, out = _brief(tmp_path, CHECKBOX_PLAN, "1.1")
    code = main(
        ["--json", "brief", "--plan", str(tmp_path / "plan.md"), "--task", "9.9", "--out", str(out)]
    )
    assert code == 2
    payload = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert payload["ok"] is False
    assert payload["error"] == "no task '9.9' in plan"


def test_task_not_found_lists_the_key():
    with pytest.raises(brief.TaskNotFound) as excinfo:
        brief.find_task(SECTION_PLAN, "7")
    assert str(excinfo.value) == "no task '7' in plan"


INDENTED_PLAN = (
    "# Tasks\n"
    "\n"
    "  - [ ] 1.1 Indented task\n"
    "    body\n"
    "  - [ ] 1.2 Sibling\n"
    "    other\n"
)


def test_indented_sibling_stops_the_body(tmp_path):
    code, out = _brief(tmp_path, INDENTED_PLAN, "1.1")
    assert code == 0
    assert (
        (out / "task-1.1-brief.md").read_text(encoding="utf-8")
        == "  - [ ] 1.1 Indented task\n    body\n"
    )


def test_blank_line_inside_the_body_stays(tmp_path):
    code, out = _brief(tmp_path, CHECKBOX_PLAN, "2.3")
    assert code == 0
    text = (out / "task-2.3-brief.md").read_text(encoding="utf-8")
    assert text == CHECKBOX_2_3_EXPECTED


def test_brief_creates_nested_out_directories(tmp_path):
    plan = tmp_path / "tasks.md"
    plan.write_text(CHECKBOX_PLAN, encoding="utf-8")
    out = tmp_path / "deep" / "nested" / "out"
    assert main(["brief", "--plan", str(plan), "--task", "1.1", "--out", str(out)]) == 0
    assert (out / "task-1.1-brief.md").is_file()


def test_missing_plan_error_names_the_plan(tmp_path, capsys):
    missing = tmp_path / "nope.md"
    code = main(
        ["--json", "brief", "--plan", str(missing), "--task", "1", "--out", str(tmp_path / "o")]
    )
    assert code == 2
    payload = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert payload["error"].startswith("cannot read plan")
    assert "XX" not in payload["error"]


def test_non_numeric_task_id_message_is_pinned():
    with pytest.raises(brief.TaskNotFound) as excinfo:
        brief._task_key("one")
    assert str(excinfo.value) == "non-numeric task id: 'one'"


FENCED_SECTION_PLAN = (
    "### Task 4: Shell steps\n"
    "\n"
    "Run this:\n"
    "\n"
    "```sh\n"
    "# not a heading\n"
    "deploy --force\n"
    "```\n"
    "\n"
    "#### A deeper sub-heading stays\n"
    "\n"
    "Done.\n"
)


def test_fenced_comment_does_not_end_a_section_body(tmp_path):
    code, out = _brief(tmp_path, FENCED_SECTION_PLAN, "4")
    assert code == 0
    text = (out / "task-4-brief.md").read_text(encoding="utf-8")
    assert "# not a heading" in text
    assert "deploy --force" in text
    assert "A deeper sub-heading stays" in text
    assert "Done." in text


FENCED_CHECKBOX_PLAN = (
    "- [ ] 6.1 Fenced body\n"
    "```sh\n"
    "# literal task text below\n"
    "- [ ] 9.9 not a task\n"
    "```\n"
    "after the fence\n"
)


def test_fenced_checkbox_text_does_not_end_a_body(tmp_path):
    code, out = _brief(tmp_path, FENCED_CHECKBOX_PLAN, "6.1")
    assert code == 0
    text = (out / "task-6.1-brief.md").read_text(encoding="utf-8")
    assert "- [ ] 9.9 not a task" in text
    # The dedented line after the closing fence ends the body, per the
    # documented dedent rule.
    assert "after the fence" not in text


def test_out_dir_that_is_a_file_exits_two(tmp_path, capsys):
    plan = tmp_path / "tasks.md"
    plan.write_text(CHECKBOX_PLAN, encoding="utf-8")
    blocker = tmp_path / "out"
    blocker.write_text("not a directory\n", encoding="utf-8")
    code = main(["--json", "brief", "--plan", str(plan), "--task", "1.1", "--out", str(blocker)])
    assert code == 2
    payload = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert payload["error"].startswith("cannot write brief")


TILDE_SECTION_PLAN = (
    "### Task 5: Tilde fence\n"
    "\n"
    "~~~sh\n"
    "# still not a heading\n"
    "~~~\n"
)


def test_tilde_fences_protect_the_body_too(tmp_path):
    code, out = _brief(tmp_path, TILDE_SECTION_PLAN, "5")
    assert code == 0
    text = (out / "task-5-brief.md").read_text(encoding="utf-8")
    assert "# still not a heading" in text


def test_blank_line_inside_a_fence_keeps_the_fence_alive(tmp_path):
    plan = (
        "- [ ] 7.1 Fenced with blanks\n"
        "```sh\n"
        "echo hi\n"
        "\n"
        "# heading-ish after a blank\n"
        "- [ ] 8.8 not a task\n"
        "```\n"
    )
    code, out = _brief(tmp_path, plan, "7.1")
    assert code == 0
    text = (out / "task-7.1-brief.md").read_text(encoding="utf-8")
    assert "# heading-ish after a blank" in text
    assert "- [ ] 8.8 not a task" in text


def test_comment_after_content_inside_a_fence_stays(tmp_path):
    plan = (
        "### Task 9: Echo then comment\n"
        "\n"
        "```sh\n"
        "echo hi\n"
        "# heading-ish after content\n"
        "```\n"
    )
    code, out = _brief(tmp_path, plan, "9")
    assert code == 0
    assert "# heading-ish after content" in (out / "task-9-brief.md").read_text(encoding="utf-8")
