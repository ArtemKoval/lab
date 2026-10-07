import argparse
import json

import pytest

from apfel_eval import run
from apfel_eval.run import Result

QUESTION = "What is the capital of France?"


def result(**changes):
    values = {
        "question": QUESTION,
        "expected": "Paris",
        "actual": "Paris",
        "score": 0.8,
        "passed": True,
        "reason": "fake reason",
        "error": None,
    }
    return Result(**{**values, **changes})


def error_result(message, **changes):
    return result(actual=None, score=None, passed=False, reason=None, error=message, **changes)


# --- rows


def test_row_for_a_passed_answer():
    assert run.format_row(result()) == (
        "PASS 0.80 | What is the capital of France? | expected: Paris | answer: Paris"
    )


def test_row_for_a_failed_answer():
    row = run.format_row(result(score=0.0, passed=False, actual="Rome"))
    assert row == "FAIL 0.00 | What is the capital of France? | expected: Paris | answer: Rome"


@pytest.mark.parametrize(
    ("score", "text"), [(0.5, "0.50"), (1.0, "1.00"), (0.123, "0.12"), (0.999, "1.00")]
)
def test_score_has_two_decimals(score, text):
    assert run.format_row(result(score=score)).startswith(f"PASS {text} | ")


def test_row_for_an_error():
    row = run.format_row(
        error_result(
            "APIStatusError: context full",
            question="What is the chemical symbol for water?",
            expected="H2O",
        )
    )
    assert row == (
        "ERROR n/a | What is the chemical symbol for water? | expected: H2O | "
        "error: APIStatusError: context full"
    )


@pytest.mark.parametrize(
    ("answer", "text"),
    [("Paris\nFrance", "Paris France"), ("Paris\r\nFrance", "Paris France"), ("a\n\nb", "a  b")],
)
def test_line_break_in_the_answer_becomes_a_space(answer, text):
    row = run.format_row(result(actual=answer))
    assert row.endswith(f"| answer: {text}")
    assert len(row.splitlines()) == 1


def test_line_break_in_the_error_becomes_a_space():
    row = run.format_row(error_result("Error: line one\nline two"))
    assert row.endswith("| error: Error: line one line two")
    assert len(row.splitlines()) == 1


# --- summary and exit code


def test_summary_counts_each_verdict():
    results = [
        result(),
        result(),
        result(score=0.0, passed=False),
        error_result("E: x"),
    ]
    assert run.summarize(results) == {"total": 4, "passed": 2, "failed": 1, "errors": 1}


def test_summary_of_no_results_is_zero():
    assert run.summarize([]) == {"total": 0, "passed": 0, "failed": 0, "errors": 0}


def test_summary_line():
    summary = {"total": 4, "passed": 4, "failed": 0, "errors": 0}
    assert run.format_summary(summary) == "total=4 passed=4 failed=0 errors=0"


@pytest.mark.parametrize(
    ("summary", "code"),
    [
        ({"total": 4, "passed": 4, "failed": 0, "errors": 0}, 0),
        ({"total": 4, "passed": 3, "failed": 1, "errors": 0}, 1),
        ({"total": 4, "passed": 3, "failed": 0, "errors": 1}, 2),
        ({"total": 4, "passed": 2, "failed": 1, "errors": 1}, 2),
    ],
)
def test_exit_code(summary, code):
    assert run.exit_code(summary) == code


# --- JSON


def test_json_report_layout():
    args = argparse.Namespace(base_url="http://x:1/v1", model="m", threshold=0.5)
    assert run.format_json(args, []) == """\
{
  "base_url": "http://x:1/v1",
  "model": "m",
  "threshold": 0.5,
  "results": [],
  "summary": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": 0
  }
}"""


def test_json_report_has_the_documented_keys():
    args = argparse.Namespace(base_url="http://x:1/v1", model="m", threshold=0.5)
    report = json.loads(run.format_json(args, [result(), error_result("E: x")]))
    assert set(report) == {"base_url", "model", "threshold", "results", "summary"}
    assert (report["base_url"], report["model"], report["threshold"]) == ("http://x:1/v1", "m", 0.5)
    assert report["summary"] == {"total": 2, "passed": 1, "failed": 0, "errors": 1}
    keys = {"question", "expected", "actual", "score", "passed", "reason", "error"}
    assert all(set(item) == keys for item in report["results"])
    assert report["results"][0] == {
        "question": QUESTION,
        "expected": "Paris",
        "actual": "Paris",
        "score": 0.8,
        "passed": True,
        "reason": "fake reason",
        "error": None,
    }
    assert report["results"][1]["score"] is None
    assert report["results"][1]["passed"] is False
    assert report["results"][1]["error"] == "E: x"
