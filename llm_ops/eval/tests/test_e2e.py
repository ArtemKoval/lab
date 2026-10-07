"""Tests against a real apfel server. Start it on the host with `apfel --serve`.

Run them with: APFEL_E2E=1 pytest -m e2e
They check the structure of the results. They do not check the exact score of the judge.
"""

import json
import os

import pytest
from pydantic import BaseModel

from apfel_eval import run
from apfel_eval.judge import ApfelJudge

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("APFEL_E2E") != "1", reason="set APFEL_E2E=1"),
]

# The fixture that isolates the environment removes APFEL_BASE_URL, so read it here.
BASE_URL = os.environ.get("APFEL_BASE_URL", run.DEFAULT_BASE_URL)


class Item(BaseModel):
    name: str


class Basket(BaseModel):
    items: list[Item]


@pytest.fixture(scope="module")
def judge():
    return ApfelJudge(BASE_URL)


def test_server_lists_the_apple_model(judge):
    assert "apple-foundationmodel" in judge.ping()


def test_text_call(judge):
    assert "Paris" in judge.generate("What is the capital of France? Answer in one word.")


def test_nested_schema_call(judge):
    basket = judge.generate("List two fruits as items with a name.", Basket)
    assert isinstance(basket, Basket)
    assert len(basket.items) >= 1


def test_right_answer_scores_higher_than_a_wrong_answer(judge):
    metric = run.build_metric(judge, 0.5)
    right = run.run_case(judge, metric, run.cases()[0])
    wrong = run.run_case(judge, metric, run.Case("What is the capital of Spain?", "Paris"))
    assert right.error is None
    assert wrong.error is None
    assert 0 <= wrong.score < right.score <= 1


def test_full_run_gives_four_results_without_errors(capsys):
    code = run.main(["--base-url", BASE_URL, "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code in (0, 1)
    assert len(report["results"]) == 4
    assert report["summary"]["errors"] == 0
