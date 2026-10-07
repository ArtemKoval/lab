import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

import httpx2
import pytest
from fake_apfel import ANSWERS, FakeApfel, completion

from apfel_eval import run

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = list(ANSWERS)
SECOND = "How many days are in a leap year?"
DEFAULT_URL = "http://host.docker.internal:11434/v1"
ALL_PASS_ROWS = [
    "PASS 0.80 | What is the capital of France? | expected: Paris | answer: Paris",
    "PASS 0.80 | How many days are in a leap year? | expected: 366 | answer: 366",
    "PASS 0.80 | What is the chemical symbol for water? | expected: H2O | answer: H2O",
    "PASS 0.80 | Who wrote the play Romeo and Juliet? | expected: William Shakespeare "
    "| answer: William Shakespeare",
]


HELP = """\
usage: python -m apfel_eval.run [-h] [--base-url BASE_URL] [--model MODEL]
                                [--threshold THRESHOLD] [--json]

Ask four questions and score the answers. The apfel server is the judge.

options:
  -h, --help            show this help message and exit
  --base-url BASE_URL   the base URL of the apfel server (default:
                        APFEL_BASE_URL or
                        http://host.docker.internal:11434/v1)
  --model MODEL         the model name (apple-foundationmodel)
  --threshold THRESHOLD
                        the lowest score that passes, from 0 to 1 (0.5)
  --json                print one JSON document
"""


def lines(capsys):
    return capsys.readouterr().out.splitlines()


def test_help_text(monkeypatch):
    monkeypatch.setenv("COLUMNS", "80")
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert run.build_parser().format_help() == HELP


# --- the questions and the report


def test_all_answers_pass(serve, fake, capsys):
    serve(fake)
    assert run.main([]) == 0
    assert lines(capsys) == [*ALL_PASS_ROWS, "total=4 passed=4 failed=0 errors=0"]


def test_server_gets_the_questions_in_order_one_at_a_time(serve, fake):
    serve(fake)
    run.main([])
    asked = [prompt.rsplit("Question: ", 1)[1] for prompt in fake.prompts()]
    assert asked == QUESTIONS
    assert fake.max_open == 1
    assert all(body["temperature"] == 0 for body in fake.bodies)


def test_one_run_makes_one_ping_and_eight_model_calls(serve, fake):
    serve(fake)
    run.main([])
    paths = [request.url.path for request in fake.requests]
    assert paths.count("/v1/models") == 1
    assert paths[0] == "/v1/models"
    assert paths.count("/v1/chat/completions") == 8


def test_one_answer_fails(serve, capsys):
    fake = FakeApfel(
        answers={**ANSWERS, "Who wrote the play Romeo and Juliet?": "Christopher Marlowe"},
        score=lambda prompt: 0 if "Marlowe" in prompt else 8,
    )
    serve(fake)
    assert run.main([]) == 1
    output = lines(capsys)
    assert output[3] == (
        "FAIL 0.00 | Who wrote the play Romeo and Juliet? | expected: William Shakespeare "
        "| answer: Christopher Marlowe"
    )
    assert output[-1] == "total=4 passed=3 failed=1 errors=0"


def test_error_in_one_question_does_not_stop_the_others(serve, capsys):
    fake = FakeApfel(fail_questions=(SECOND,))
    serve(fake)
    assert run.main([]) == 2
    output = lines(capsys)
    assert output[1].startswith(
        "ERROR n/a | How many days are in a leap year? | expected: 366 | "
        "error: BadRequestError: Error code: 400 - "
    )
    assert "context window is full" in output[1]
    assert [output[0], *output[2:4]] == [ALL_PASS_ROWS[0], *ALL_PASS_ROWS[2:]]
    assert output[-1] == "total=4 passed=3 failed=0 errors=1"
    assert len(fake.prompts()) == 4


def test_one_fail_and_one_error_exit_with_2(serve, capsys):
    fake = FakeApfel(
        answers={**ANSWERS, "Who wrote the play Romeo and Juliet?": "Christopher Marlowe"},
        score=lambda prompt: 0 if "Marlowe" in prompt else 8,
        fail_questions=(SECOND,),
    )
    serve(fake)
    assert run.main([]) == 2
    assert lines(capsys)[-1] == "total=4 passed=2 failed=1 errors=1"


def test_json_report(serve, fake, capsys):
    serve(fake)
    assert run.main(["--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert set(report) == {"base_url", "model", "threshold", "results", "summary"}
    assert report["base_url"] == DEFAULT_URL
    assert report["model"] == "apple-foundationmodel"
    assert report["threshold"] == 0.5
    assert report["summary"] == {"total": 4, "passed": 4, "failed": 0, "errors": 0}
    assert [item["question"] for item in report["results"]] == QUESTIONS
    assert [item["actual"] for item in report["results"]] == list(ANSWERS.values())
    assert all(item["score"] == 0.8 and item["passed"] for item in report["results"])


def test_json_report_for_a_question_with_an_error(serve, capsys):
    serve(FakeApfel(fail_questions=(SECOND,)))
    assert run.main(["--json"]) == 2
    item = json.loads(capsys.readouterr().out)["results"][1]
    assert (item["score"], item["passed"], item["actual"]) == (None, False, None)
    assert "400" in item["error"]


def test_each_question_gets_its_own_metric(serve, fake, monkeypatch):
    built = []
    real = run.build_metric

    def build(*args, **kwargs):
        built.append(real(*args, **kwargs))
        return built[-1]

    monkeypatch.setattr(run, "build_metric", build)
    serve(fake)
    run.main([])
    assert len(built) == 4
    assert len({id(metric) for metric in built}) == 4


def test_invalid_score_reply_does_not_change_the_next_question(serve, capsys):
    fake = FakeApfel()
    scores = []

    def handler(request):
        if b"ReasonScore" in request.content:
            scores.append(request)
            if len(scores) == 1:
                return completion("not json")
        return fake(request)

    serve(handler)
    assert run.main([]) == 2
    output = lines(capsys)
    assert output[0].startswith("ERROR n/a | What is the capital of France? | expected: Paris | ")
    assert output[1:4] == ALL_PASS_ROWS[1:]
    assert output[-1] == "total=4 passed=3 failed=0 errors=1"


# --- settings


def first_url(fake):
    return str(fake.requests[0].url)


def test_default_base_url_and_host_header(serve, fake):
    serve(fake)
    run.main([])
    assert first_url(fake) == f"{DEFAULT_URL}/models"
    assert fake.requests[0].headers["host"] == "localhost:11434"


def test_option_wins_over_the_variable(serve, fake, monkeypatch):
    monkeypatch.setenv("APFEL_BASE_URL", "http://variable:1/v1")
    serve(fake)
    run.main(["--base-url", "http://option:2/v1"])
    assert first_url(fake) == "http://option:2/v1/models"


def test_variable_wins_over_the_default(serve, fake, monkeypatch):
    monkeypatch.setenv("APFEL_BASE_URL", "http://variable:1/v1")
    serve(fake)
    run.main([])
    assert first_url(fake) == "http://variable:1/v1/models"


def test_env_file_sets_the_base_url(serve, fake):
    Path(".env").write_text("APFEL_BASE_URL=http://dotenv:3/v1\n")
    serve(fake)
    run.main([])
    assert first_url(fake) == "http://dotenv:3/v1/models"


def test_shell_wins_over_the_env_file(serve, fake, monkeypatch):
    Path(".env").write_text("APFEL_BASE_URL=http://dotenv:3/v1\n")
    monkeypatch.setenv("APFEL_BASE_URL", "http://shell:4/v1")
    serve(fake)
    run.main([])
    assert first_url(fake) == "http://shell:4/v1/models"


def test_env_file_in_another_folder_is_not_read(serve, fake, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    (other / ".env").write_text("APFEL_BASE_URL=http://other:5/v1\n")
    serve(fake)
    run.main([])
    assert first_url(fake) == f"{DEFAULT_URL}/models"


def test_token_comes_from_the_variable(serve, fake, monkeypatch):
    monkeypatch.setenv("APFEL_TOKEN", "secret")
    serve(fake)
    run.main([])
    assert {r.headers["authorization"] for r in fake.requests} == {"Bearer secret"}


def test_token_comes_from_the_env_file(serve, fake):
    Path(".env").write_text("APFEL_TOKEN=filetoken\n")
    serve(fake)
    run.main([])
    assert {r.headers["authorization"] for r in fake.requests} == {"Bearer filetoken"}


def test_no_token_uses_the_placeholder(serve, fake):
    serve(fake)
    run.main([])
    assert {r.headers["authorization"] for r in fake.requests} == {"Bearer apfel-no-token"}


def test_model_option_names_the_model(serve, fake):
    serve(fake)
    run.main(["--model", "model-9"])
    assert {body["model"] for body in fake.bodies} == {"model-9"}


def test_default_model_is_the_apple_model(serve, fake):
    serve(fake)
    run.main([])
    assert {body["model"] for body in fake.bodies} == {"apple-foundationmodel"}


def test_openai_key_is_never_sent(serve, fake, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret")
    serve(fake)
    assert run.main([]) == 0
    sent = "".join(str(dict(r.headers)) + r.content.decode() for r in fake.requests)
    assert "sk-secret" not in sent


# --- the threshold


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("1.5", "argument --threshold: '1.5' is not from 0 to 1"),
        ("-0.1", "argument --threshold: '-0.1' is not from 0 to 1"),
        ("nan", "argument --threshold: 'nan' is not from 0 to 1"),
        ("inf", "argument --threshold: 'inf' is not from 0 to 1"),
        ("high", "argument --threshold: 'high' is not a number"),
        ("", "argument --threshold: '' is not a number"),
    ],
)
def test_bad_threshold_is_a_usage_error(serve, fake, capsys, value, message):
    serve(fake)
    with pytest.raises(SystemExit) as stop:
        run.main([f"--threshold={value}"])
    assert stop.value.code == 2
    error = capsys.readouterr().err
    assert error.startswith("usage: python -m apfel_eval.run")
    assert error.endswith(f"python -m apfel_eval.run: error: {message}\n")
    assert fake.requests == []


def test_threshold_0_and_1_are_valid(serve, fake, capsys):
    serve(fake)
    assert run.main(["--threshold", "0"]) == 0
    assert run.main(["--threshold", "1"]) == 1
    rows = lines(capsys)
    assert rows[4] == "total=4 passed=4 failed=0 errors=0"
    assert rows[-1] == "total=4 passed=0 failed=4 errors=0"


def test_threshold_is_in_the_json_report(serve, fake, capsys):
    serve(fake)
    run.main(["--json", "--threshold", "0.7"])
    assert json.loads(capsys.readouterr().out)["threshold"] == 0.7


# --- the server


def test_server_error_status_stops_the_run(serve, capsys):
    fake = FakeApfel(status=403)
    serve(fake)
    assert run.main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        f"Cannot use the apfel server at {DEFAULT_URL}: PermissionDeniedError: "
        "Error code: 403 - {'error': {'message': 'fake apfel error', 'type': 'fake'}}\n"
        "Start the server on the host with: apfel --serve\n"
    )
    assert len(fake.requests) == 1


def test_server_that_is_off_stops_the_run(capsys):
    assert run.main(["--base-url", "http://127.0.0.1:1/v1"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "http://127.0.0.1:1/v1" in captured.err
    assert "APIConnectionError" in captured.err
    assert "apfel --serve" in captured.err


def test_base_url_with_a_bad_port_stops_the_run(capsys):
    assert run.main(["--base-url", "http://host:abc/v1"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "http://host:abc/v1" in captured.err
    assert "ValueError" in captured.err


def test_reply_that_is_not_a_model_list_stops_the_run(serve, capsys):
    headers = {"content-type": "text/html"}
    page = httpx2.Response(200, text="<html>not apfel</html>", headers=headers)
    serve(lambda request: page)
    assert run.main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(f"Cannot use the apfel server at {DEFAULT_URL}: ")
    assert captured.err.endswith("Start the server on the host with: apfel --serve\n")


def test_base_url_with_a_control_character_stops_the_run(capsys):
    assert run.main(["--base-url", "http://127.0.0.1:1/v1\t"]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("Cannot use the apfel server at http://127.0.0.1:1/v1\t: ")
    assert "apfel --serve" in captured.err


def test_env_file_that_is_not_text_stops_the_run(serve, fake, capsys):
    Path(".env").write_bytes(b"APFEL_TOKEN=caf\xe9\n")
    serve(fake)
    assert run.main([]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("Cannot read the .env file: UnicodeDecodeError: ")
    assert fake.requests == []


# --- started as a module


def test_module_entry_exits_with_the_code_of_main(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["apfel_eval.run", "--threshold", "2"])
    monkeypatch.delitem(sys.modules, "apfel_eval.run")
    with pytest.raises(SystemExit) as stop:
        runpy.run_module("apfel_eval.run", run_name="__main__")
    assert stop.value.code == 2


def test_module_in_a_new_process_exits_2_when_the_server_is_off():
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    done = subprocess.run(
        [sys.executable, "-m", "apfel_eval.run", "--base-url", "http://127.0.0.1:1/v1"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert done.returncode == 2
    assert done.stdout == ""
    assert "apfel --serve" in done.stderr
