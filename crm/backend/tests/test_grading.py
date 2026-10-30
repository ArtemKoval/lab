"""The judge grades an evaluation's copies as the evaluation finishes."""

import json
import time

import httpx
import pytest
from sqlalchemy import func, select, update

from backend.database import engine, grades, worker_decisions, runs
from backend.tests.case_requests import decide, start
from backend.tests.judging import answer
from backend.tests.run_requests import (
    create_evaluation,
    fail_run,
    finish,
    get_evaluation,
)


def count_grades():
    with engine().connect() as db:
        return db.execute(select(func.count()).select_from(grades)).scalar_one()


def decide_all_but_one(client, evaluation, evaluation_set="held_out"):
    """Decide every copy as its worker did, but leave the first undecided."""
    copies = [c["case_id"] for c in evaluation["cases"]]
    with engine().connect() as db:
        rows = db.execute(
            select(worker_decisions).where(
                worker_decisions.c.evaluation_set == evaluation_set
            )
        ).mappings()
        workers = {row["case_id"]: row for row in rows}
    for copy in copies[1:]:
        worker = workers[copy.rsplit("-E", 1)[0]]
        start(client, copy)
        decide(client, copy, worker["decision"], worker["award"])
    return copies


def test_seeding_stores_the_workers_reasons_and_references():
    with engine().connect() as db:
        rows = db.execute(select(worker_decisions)).mappings().all()
    assert len(rows) == 50
    assert all(row["reason"] and row["reference"] for row in rows)


def test_nothing_the_case_agent_reads_holds_a_reason_or_a_reference(client):
    with engine().connect() as db:
        query = select(worker_decisions.c.reason, worker_decisions.c.reference)
        texts = [text for row in db.execute(query) for text in row]
    evaluation = create_evaluation(client, "evaluation").json()
    copies = decide_all_but_one(client, evaluation, "evaluation")
    finished = finish(client, evaluation["run_id"]).json()
    seen = json.dumps(
        [
            client.get("/api/cases/CLM-1001").json(),
            client.get("/api/cases").json(),
            client.get("/api/versions/current").json(),
            client.get(f"/api/cases/{copies[1]}").json(),
            finished,
        ]
    )
    assert not any(text in seen for text in texts)


def test_an_evaluation_is_graded_as_it_finishes(client, judged):
    evaluation = create_evaluation(client).json()
    copies = decide_all_but_one(client, evaluation)
    finished = finish(client, evaluation["run_id"])
    assert finished.status_code == 200
    assert "grade" not in finished.text

    scored = get_evaluation(client, evaluation["run_id"])
    by_copy = {c["case_id"]: c for c in scored["cases"]}
    assert by_copy[copies[0]]["grade"] == {
        "score": 0.0,
        "letter": "F",
        "same_grounds": 0.0,
        "same_section": 0.0,
        "cost": 0.0,
    }
    for copy in copies[1:]:
        assert by_copy[copy]["grade"]["letter"] == "B"
    assert len(judged) == 4
    assert scored["measures"]["grade"] == pytest.approx((0 + 4 * 2.2) / 5)
    assert scored["judge_cost"] == pytest.approx(4 * 0.00002)
    assert scored["model_cost"] == 0
    request = judged[0]["state"]
    assert set(request["agent"]) == {"decision", "reason", "section"}
    assert set(request["worker"]) == {"decision", "reason", "reference"}


def test_a_case_the_judge_cant_grade_is_left_out_of_the_average(client, judge_answers):
    answers = iter([httpx.Response(500, json={"error": "Down"})])

    def first_fails(request):
        return next(answers, httpx.Response(200, json=answer(score=3.0)))

    judge_answers(first_fails)
    evaluation = create_evaluation(client).json()
    decide_all_but_one(client, evaluation)
    finish(client, evaluation["run_id"])
    scored = get_evaluation(client, evaluation["run_id"])
    assert [c["grade"] is None for c in scored["cases"]].count(True) == 1
    assert scored["measures"]["grade"] == pytest.approx((0 + 3 * 3.0) / 4)


def test_an_evaluation_with_none_graded_has_no_grade(client, judge_answers):
    judge_answers(lambda request: httpx.Response(500, json={"error": "Down"}))
    evaluation = create_evaluation(client).json()
    for copy in evaluation["cases"]:
        start(client, copy["case_id"])
        decide(client, copy["case_id"], "refer", 0)
    finish(client, evaluation["run_id"])
    assert get_evaluation(client, evaluation["run_id"])["measures"]["grade"] is None


def test_grading_25_copies_runs_them_at_once(client, judge_answers):
    def slow(request):
        time.sleep(0.3)
        return httpx.Response(200, json=answer())

    judge_answers(slow)
    evaluation = create_evaluation(client, tiny=False).json()
    for copy in evaluation["cases"]:
        start(client, copy["case_id"])
        decide(client, copy["case_id"], "refer", 0)
    started = time.monotonic()
    assert finish(client, evaluation["run_id"]).status_code == 200
    assert time.monotonic() - started < 2
    assert count_grades() == 25


def test_a_student_on_a_free_model_has_no_judge(client, judged, monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "openrouter/free")
    evaluation = create_evaluation(client).json()
    decide_all_but_one(client, evaluation)
    finish(client, evaluation["run_id"])
    assert judged == []
    cases = get_evaluation(client, evaluation["run_id"])["cases"]
    assert {c["grade"] is None for c in cases} == {True}


def test_a_stopped_evaluation_isnt_graded(client, judged):
    evaluation = create_evaluation(client).json()
    decide_all_but_one(client, evaluation)
    fail_run(client, evaluation["run_id"])
    finished = finish(client, evaluation["run_id"])
    assert (finished.status_code, finished.json()["status"]) == (200, "stopped")
    assert (judged, count_grades()) == ([], 0)


def test_an_evaluation_stopped_while_it_is_graded_stays_stopped(client, judge_answers):
    evaluation = create_evaluation(client).json()
    decide_all_but_one(client, evaluation)

    def stopped_meanwhile(request):
        with engine().begin() as db:
            db.execute(update(runs).values(status="stopped"))
        return httpx.Response(200, json=answer())

    judge_answers(stopped_meanwhile)
    finished = finish(client, evaluation["run_id"])
    assert (finished.status_code, finished.json()["status"]) == (200, "stopped")
    assert get_evaluation(client, evaluation["run_id"])["status"] == "stopped"
    assert count_grades() == 0
