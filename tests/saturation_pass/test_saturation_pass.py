"""Behavior tests for the saturation pass CLI in saturation_pass."""

import json
import sys

from saturation_pass import (
    TOOL_TABLE,
    compare,
    load_store,
    main,
    module_scores,
    parse_table,
    run_mutator,
    write_store,
    _write_report,
)

TABLE = """Some header noise
more noise
Function                       Namespace                                  Killed  Survived  Uncovered  Sites   Score
----------------------------------------------------------------------------------------------------------
_check_word_hits               tools.spec_ste_check.spec_ste_check.rules       2         0          0      2 100.0%
_hide_spans                    tools.spec_ste_check.spec_ste_check.hook        4         0          0      4 100.0%
_print_human                   tools.spec_ste_check.spec_ste_check.hook        2         0          1      3 100.0%
check_tenses                   tools.spec_ste_check.spec_ste_check.rules       1         0          0      1 100.0%
prose_sentences                tools.spec_ste_check.spec_ste_check.rules       5         1          0      6  83.3%
word_count                     tools.spec_ste_check.spec_ste_check.cli         1         0          0      1 100.0%
----------------------------------------------------------------------------------------------------------
Total                                                               15         1          1     17  93.8%
"""

NA_TABLE = TABLE.replace(
    next(line for line in TABLE.splitlines()
         if line.startswith("word_count")),
    "word_count tools.spec_ste_check.spec_ste_check.cli 0 0 1 1 n/a",
)

STAMP = "2026-11-08T09:00:00+00:00"
PAST_STAMP = "2026-11-08T08:00:00+00:00"


def clean_modules():
    """Return the module scores the clean table reports."""
    return module_scores("spec_ste_check", TABLE)


def seeded_store():
    """Return one store at the clean scores with an older stamp."""
    return {
        "schema": 1,
        "tools": {
            "spec_ste_check": {
                "stamp": PAST_STAMP,
                "modules": clean_modules(),
            },
        },
    }


def seeded(tmp_path):
    """Write the seeded store and the coverage sentinel. Return paths."""
    store_path = tmp_path / "scores.json"
    write_store(store_path, seeded_store())
    coverage = tmp_path / "lcov.info"
    coverage.write_text("SF:x\n", encoding="utf-8")
    return store_path, coverage


def ok_mutator(argv):
    """Fake mutator that prints the clean table and exits 0."""
    return 0, TABLE, ""


def test_parse_table_groups_rows_by_namespace():
    rows = parse_table(TABLE)
    assert rows["tools.spec_ste_check.spec_ste_check.rules"] == {
        "killed": 8, "survived": 1, "uncovered": 0, "sites": 9,
    }
    assert rows["tools.spec_ste_check.spec_ste_check.hook"] == {
        "killed": 6, "survived": 0, "uncovered": 1, "sites": 7,
    }


def test_parse_table_skips_header_separator_and_total():
    rows = parse_table(TABLE)
    assert "Function" not in rows
    assert "Total" not in rows
    assert len(rows) == 3


def test_parse_table_of_an_empty_run_carries_no_rows():
    assert parse_table("No functions to mutate.\n") == {}


def test_module_scores_compute_one_decimal_scores():
    scores = module_scores("spec_ste_check", TABLE)
    assert scores["tools.spec_ste_check.spec_ste_check.rules"] == {
        "sites": 9, "score": 88.9,
    }
    assert scores["tools.spec_ste_check.spec_ste_check.hook"] == {
        "sites": 7, "score": 100.0,
    }


def test_module_scores_of_scoreless_rows_give_none():
    scores = module_scores("spec_ste_check", NA_TABLE)
    assert scores["tools.spec_ste_check.spec_ste_check.cli"] == {
        "sites": 1, "score": None,
    }


def test_module_scores_omit_siteless_namespaces():
    siteless = TABLE.replace(
        next(line for line in TABLE.splitlines()
             if line.startswith("word_count")),
        "word_count tools.spec_ste_check.spec_ste_check.cli 0 0 0 0 n/a",
    )
    scores = module_scores("spec_ste_check", siteless)
    assert "tools.spec_ste_check.spec_ste_check.cli" not in scores
    assert scores["tools.spec_ste_check.spec_ste_check.rules"] == {
        "sites": 9, "score": 88.9,
    }


STORED = {
    "tools.spec_ste_check.spec_ste_check.rules": {"sites": 9, "score": 88.9},
    "tools.spec_ste_check.spec_ste_check.cli": {"sites": 1, "score": 100.0},
}


def test_compare_names_a_drop_with_both_scores():
    run = {"tools.spec_ste_check.spec_ste_check.rules": {
        "sites": 9, "score": 77.8}}
    verdicts = compare("spec_ste_check", run, STORED)
    drop = [v for v in verdicts if v["verdict"] == "drop"]
    assert drop == [{
        "tool": "spec_ste_check",
        "module": "tools.spec_ste_check.spec_ste_check.rules",
        "verdict": "drop", "stored": 88.9, "run": 77.8,
    }]


def test_compare_records_a_new_module_without_a_refusal():
    run = dict(STORED)
    run["tools.spec_ste_check.spec_ste_check.hook"] = {
        "sites": 7, "score": 100.0}
    verdicts = compare("spec_ste_check", run, STORED)
    assert [v["verdict"] for v in verdicts] == ["hold", "hold", "new"]


def test_compare_marks_a_scoreless_module_as_a_violation():
    run = {"tools.spec_ste_check.spec_ste_check.cli": {
        "sites": 1, "score": None}}
    verdicts = compare("spec_ste_check", run, STORED)
    assert verdicts == [{
        "tool": "spec_ste_check",
        "module": "tools.spec_ste_check.spec_ste_check.cli",
        "verdict": "no-score", "stored": 100.0, "run": None,
    }]


def test_load_store_of_a_missing_file_gives_none(tmp_path):
    assert load_store(tmp_path / "absent.json") is None


def test_load_store_of_corrupt_json_gives_none(tmp_path):
    path = tmp_path / "scores.json"
    path.write_text("not json {", encoding="utf-8")
    assert load_store(path) is None


def test_run_mutator_returns_code_stdout_and_stderr():
    code, out, err = run_mutator(
        [sys.executable, "-c", "print('table out'); raise SystemExit(3)"])
    assert (code, out.strip(), err) == (3, "table out", "")


def test_store_roundtrip_keeps_the_schema(tmp_path):
    path = tmp_path / "scores.json"
    write_store(path, seeded_store())
    assert load_store(path) == seeded_store()


def test_store_write_twice_to_the_same_path_succeeds(tmp_path):
    path = tmp_path / "scores.json"
    write_store(path, seeded_store())
    write_store(path, seeded_store())
    assert load_store(path) == seeded_store()


def test_report_write_creates_nested_dirs(tmp_path):
    path = tmp_path / "a" / "b" / "report.json"
    _write_report(path, {"schema": 1, "tools": {}})
    assert path.is_file()


def test_report_write_twice_to_the_same_path_succeeds(tmp_path):
    path = tmp_path / "nested" / "report.json"
    report = {"schema": 1, "tools": {}}
    _write_report(path, report)
    _write_report(path, report)
    assert path.is_file()


def test_table_names_the_nine_owned_tools():
    names = [entry[0] for entry in TOOL_TABLE]
    assert names == [
        "plan_exec", "spec_ste_check", "devcontainer_init",
        "handover_telemetry", "handover_telemetry_setup",
        "dspy_gate", "dspy_gate_setup", "peak_hours_gate",
        "process_issues",
    ]


def test_main_runs_one_tool_and_exits_0(tmp_path):
    store_path, coverage = seeded(tmp_path)
    calls = []
    code = main(
        ["--tool", "spec_ste_check", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=lambda argv: calls.append(argv) or (0, TABLE, ""),
        clock=lambda: STAMP,
    )
    assert code == 0
    assert len(calls) == 1
    assert "--use-existing-coverage" in calls[0]
    assert "tests/spec_ste_check" in calls[0][-2]
    assert calls[0][-1] == "tools/spec_ste_check/spec_ste_check"


def test_main_refuses_an_unknown_tool(tmp_path, capsys):
    store_path, coverage = seeded(tmp_path)
    code = main(
        ["--tool", "nope", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=ok_mutator, clock=lambda: STAMP,
    )
    assert code == 2
    captured = capsys.readouterr().err
    assert "nope" in captured
    assert str([entry[0] for entry in TOOL_TABLE]) in captured


def test_main_missing_coverage_fails_with_the_hint(tmp_path, capsys):
    code = main(["--store", str(tmp_path / "s.json"),
                 "--coverage", str(tmp_path / "absent.info")],
                mutator=ok_mutator, clock=lambda: STAMP)
    assert code == 2
    assert "--coverage" in capsys.readouterr().err


def test_main_missing_store_fails_with_the_init_hint(tmp_path, capsys):
    coverage = tmp_path / "lcov.info"
    coverage.write_text("SF:x\n", encoding="utf-8")
    code = main(
        ["--store", str(tmp_path / "absent.json"),
         "--coverage", str(coverage)],
        mutator=ok_mutator, clock=lambda: STAMP,
    )
    assert code == 2
    assert "--init" in capsys.readouterr().err


def test_main_refuses_both_actions(tmp_path, capsys):
    store_path, coverage = seeded(tmp_path)
    code = main(
        ["--init", "--update", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=ok_mutator, clock=lambda: STAMP,
    )
    assert code == 2


def test_main_init_writes_the_baseline(tmp_path):
    store_path, coverage = seeded(tmp_path)
    store_path.unlink()
    code = main(
        ["--init", "--tool", "spec_ste_check", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=ok_mutator, clock=lambda: STAMP,
    )
    assert code == 0
    store = load_store(store_path)
    assert store["schema"] == 1
    assert store["tools"]["spec_ste_check"]["stamp"] == STAMP
    assert store["tools"]["spec_ste_check"]["modules"] == clean_modules()


def test_main_init_refuses_an_existing_store(tmp_path, capsys):
    store_path, coverage = seeded(tmp_path)
    code = main(
        ["--init", "--store", str(store_path), "--coverage", str(coverage)],
        mutator=ok_mutator, clock=lambda: STAMP,
    )
    assert code == 2
    assert str(store_path) in capsys.readouterr().err


def test_main_init_refuses_scoreless_modules(tmp_path):
    store_path, coverage = seeded(tmp_path)
    store_path.unlink()
    code = main(
        ["--init", "--store", str(store_path), "--coverage", str(coverage)],
        mutator=lambda argv: (0, NA_TABLE, ""), clock=lambda: STAMP,
    )
    assert code == 2
    assert load_store(store_path) is None


def test_main_run_fails_a_scoreless_module_against_the_store(tmp_path):
    store_path, coverage = seeded(tmp_path)
    code = main(
        ["--tool", "spec_ste_check", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=lambda argv: (0, NA_TABLE, ""), clock=lambda: STAMP,
    )
    assert code == 2


def test_main_update_rewrites_the_store_after_a_clean_run(tmp_path):
    store_path, coverage = seeded(tmp_path)
    code = main(
        ["--update", "--tool", "spec_ste_check", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=ok_mutator, clock=lambda: STAMP,
    )
    assert code == 0
    store = load_store(store_path)
    assert store["tools"]["spec_ste_check"]["stamp"] == STAMP


def test_main_update_refuses_a_violation_and_keeps_the_store(tmp_path):
    store_path, coverage = seeded(tmp_path)
    low = TABLE.replace(
        "_check_word_hits               tools.spec_ste_check"
        ".spec_ste_check.rules       2         0          0      2 100.0%",
        "_check_word_hits               tools.spec_ste_check"
        ".spec_ste_check.rules       1         1          0      2  50.0%",
    )
    code = main(
        ["--update", "--tool", "spec_ste_check", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=lambda argv: (0, low, ""), clock=lambda: STAMP,
    )
    assert code == 2
    assert load_store(store_path) == seeded_store()


def test_main_update_drops_a_stale_module(tmp_path):
    store_path, coverage = seeded(tmp_path)
    store = seeded_store()
    store["tools"]["spec_ste_check"]["modules"]["gone.rules"] = {
        "sites": 3, "score": 90.0,
    }
    write_store(store_path, store)
    code = main(
        ["--update", "--tool", "spec_ste_check", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=ok_mutator, clock=lambda: STAMP,
    )
    assert code == 0
    store = load_store(store_path)
    assert "gone.rules" not in store["tools"]["spec_ste_check"]["modules"]


def test_main_mutator_baseline_failure_fails_one_tool(tmp_path):
    store_path, coverage = seeded(tmp_path)
    report = tmp_path / "report.json"

    def failing(argv):
        if argv[-1].endswith("spec_ste_check"):
            return 2, TABLE, "baseline broke"
        return 0, TABLE, ""

    code = main(
        ["--store", str(store_path), "--coverage", str(coverage),
         "--json", str(report)],
        mutator=failing, clock=lambda: STAMP,
    )
    assert code == 2
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["tools"]["spec_ste_check"]["error"] == (
        "spec_ste_check: the mutator exited with code 2: baseline broke")
    assert data["tools"]["spec_ste_check"]["notes"] == [
        "spec_ste_check: the mutator exited with code 2: baseline broke"]


def test_main_mutator_with_no_table_fails_the_tool(tmp_path, capsys):
    store_path, coverage = seeded(tmp_path)
    code = main(
        ["--tool", "spec_ste_check", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=lambda argv: (0, "No functions to mutate.\n", ""),
        clock=lambda: STAMP,
    )
    assert code == 2
    assert "no table" in capsys.readouterr().err


def test_main_mutator_exit_three_with_held_scores_passes(tmp_path):
    store_path, coverage = seeded(tmp_path)
    code = main(
        ["--tool", "spec_ste_check", "--store", str(store_path),
         "--coverage", str(coverage)],
        mutator=lambda argv: (3, TABLE, ""), clock=lambda: STAMP,
    )
    assert code == 0


def test_main_writes_the_json_report(tmp_path):
    store_path, coverage = seeded(tmp_path)
    report = tmp_path / "report.json"
    code = main(
        ["--tool", "spec_ste_check", "--store", str(store_path),
         "--coverage", str(coverage), "--json", str(report)],
        mutator=lambda argv: (3, TABLE, ""), clock=lambda: STAMP,
    )
    assert code == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["schema"] == 1
    assert data["tools"]["spec_ste_check"]["verdicts"][0]["verdict"] == "hold"


def test_main_writes_the_json_report_twice(tmp_path):
    store_path, coverage = seeded(tmp_path)
    report = tmp_path / "nested" / "report.json"
    argv = ["--tool", "spec_ste_check", "--store", str(store_path),
            "--coverage", str(coverage), "--json", str(report)]
    main(argv, mutator=lambda argv: (3, TABLE, ""), clock=lambda: STAMP)
    code = main(argv, mutator=lambda argv: (3, TABLE, ""),
                clock=lambda: STAMP)
    assert code == 0
    assert report.is_file()
