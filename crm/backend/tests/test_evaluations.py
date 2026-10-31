import json

import pytest

from backend.tests.case_requests import (
    decide,
    record_call,
    record_time,
    sign_off,
    start,
)
from backend.tests.dashboard_reads import evaluations, read
from backend.tests.run_requests import (
    create_dispatch,
    create_evaluation,
    finish,
    get_evaluation,
    queue,
    record_cases,
)
from domains import loader

TINY_HELD_OUT = ["CLM-1114", "CLM-1106", "CLM-1112", "CLM-1104", "CLM-1110"]


def test_an_evaluation_works_copies_of_its_cases(client):
    before = queue(client)
    evaluation = create_evaluation(client).json()
    assert (evaluation["kind"], evaluation["status"]) == ("evaluation", "running")
    assert (evaluation["evaluation_set"], evaluation["tiny"]) == ("held_out", True)
    assert (evaluation["agents"], evaluation["model"]) == (5, "openai/gpt-6-luna")
    assert evaluation["reasoning_effort"] == "none"
    copies = [c["case_id"] for c in evaluation["cases"]]
    assert copies == [f"{case_id}-E1" for case_id in TINY_HELD_OUT]
    assert {c["status"] for c in evaluation["cases"]} == {"waiting"}

    copy = client.get("/api/cases/CLM-1104-E1").json()
    assert (copy["case_id"], copy["copy_of"]) == ("CLM-1104-E1", "CLM-1104")
    assert copy["evaluation_id"] == evaluation["run_id"]
    assert copy["status"] == "waiting"
    assert queue(client) == before
    assert client.get("/api/cases/CLM-1001").json()["evaluation_id"] is None


def test_the_whole_evaluation_set(client):
    evaluation = create_evaluation(client, "evaluation", tiny=False, agents=25)
    copies = evaluation.json()["cases"]
    assert len(copies) == 25
    assert copies[0]["case_id"] == "CLM-1001-E1"
    submitted = [c["submitted_on"] for c in copies]
    assert submitted == sorted(submitted)


def test_each_evaluation_numbers_its_copies(client):
    finish(client, create_evaluation(client).json()["run_id"])
    second = create_evaluation(client, "evaluation").json()
    assert [c["case_id"] for c in second["cases"]] == [
        "CLM-1015-E2",
        "CLM-1021-E2",
        "CLM-1007-E2",
        "CLM-1017-E2",
        "CLM-1020-E2",
    ]


@pytest.mark.parametrize(
    ("evaluation_set", "agents"), [("harder", 5), ("held_out", 0), ("held_out", 26)]
)
def test_an_evaluation_needs_a_known_set_and_1_to_25_agents(
    client, evaluation_set, agents
):
    response = create_evaluation(client, evaluation_set, agents=agents)
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("evaluation_set", "decisions"),
    [("evaluation", "decisions.json"), ("held_out", "held_out_decisions.json")],
)
def test_nothing_the_agent_reads_holds_the_workers_decisions(
    client, evaluation_set, decisions
):
    evaluation = create_evaluation(client, evaluation_set, tiny=False).json()
    responses = [json.dumps(evaluation)] + [
        client.get(f"/api/cases/{c['case_id']}").text for c in evaluation["cases"]
    ]
    labels = json.loads(loader.pack().evals.joinpath(decisions).read_text())
    secrets = [label["reason"] for label in labels]
    secrets += [label["reference"] for label in labels]
    for text in responses:
        assert not [secret for secret in secrets if secret in text]
        assert "worker" not in text
        assert "calculation" not in text


def test_a_copy_cant_be_signed_off(client, agent_calls):
    create_evaluation(client)
    asked = list(agent_calls)
    start(client, "CLM-1112-E1")
    decide(client, "CLM-1112-E1", "approve", 1200.0)
    held = client.get("/api/cases/CLM-1112-E1").json()
    assert held["status"] == "waiting_for_sign_off"

    response = sign_off(client, "CLM-1112-E1")
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Case CLM-1112-E1 is a copy in an evaluation and can't be signed off"
    )
    assert client.get("/api/cases/CLM-1112-E1").json() == held
    assert agent_calls == asked


def test_an_evaluations_cases_are_its_copies(client):
    run_id = create_evaluation(client).json()["run_id"]
    response = record_cases(client, run_id, "CLM-1001")
    assert response.status_code == 409
    assert response.json()["detail"] == f"Run {run_id} is not a dispatch"


def test_an_evaluation_not_yet_worked_counts_every_copy_as_a_referral(client):
    run_id = create_evaluation(client).json()["run_id"]
    [listed] = evaluations(client)
    assert (listed["run_id"], listed["size"]) == (run_id, 5)
    assert listed["measures"] == {
        "decision_accuracy": 0.2,
        "accuracy": 0.2,
        "cost_of_mistakes": 200.0,
        "straight_through": 0.0,
        "grade": None,
        "model_cost_per_case": 0.0,
        "seconds_per_case": 0.0,
        "run_seconds": None,
    }
    assert "cases" not in listed


def test_scoring_an_evaluation(client):
    run_id = create_evaluation(client).json()["run_id"]
    for original in TINY_HELD_OUT:
        copy = f"{original}-E1"
        start(client, copy)
        record_call(client, copy, run_id, cost=0.0125)
        record_time(client, copy, run_id, seconds=40)
    decide(client, "CLM-1104-E1", "approve", 250.0)
    client.post("/api/cases/CLM-1104-E1/effects/award")
    decide(client, "CLM-1106-E1", "approve", 300.0)
    decide(client, "CLM-1110-E1", "refer", 0)
    decide(client, "CLM-1112-E1", "approve", 1200.0)
    finish(client, run_id)

    evaluation = get_evaluation(client, run_id)
    measures = evaluation["measures"]
    assert (measures["decision_accuracy"], measures["accuracy"]) == (0.8, 0.4)
    assert measures["cost_of_mistakes"] == 620.0
    assert measures["straight_through"] == 0.6
    assert measures["model_cost_per_case"] == pytest.approx(0.0125)
    assert measures["seconds_per_case"] == 40.0
    assert measures["run_seconds"] >= 0
    cases = {c["copy_of"]: c for c in evaluation["cases"]}
    assert [c["right"] for c in evaluation["cases"]] == [
        False,
        False,
        False,
        True,
        True,
    ]
    held = cases["CLM-1112"]
    assert (held["status"], held["decision"], held["award"]) == (
        "waiting_for_sign_off",
        "approve",
        1200.0,
    )
    assert (held["worker_decision"], held["worker_award"]) == ("approve", 680.0)
    assert held["mistake_cost"] == 520.0
    undecided = cases["CLM-1114"]
    assert (undecided["decision"], undecided["mistake_cost"]) == (None, 50.0)
    assert cases["CLM-1104"]["reason"] == "The delay was covered."


def test_a_wrongful_approval_costs_its_award_whether_or_not_it_was_paid(client):
    run_id = create_evaluation(client, "evaluation").json()["run_id"]
    start(client, "CLM-1015-E1")
    decide(client, "CLM-1015-E1", "approve", 1350.0)
    cases = {c["copy_of"]: c for c in get_evaluation(client, run_id)["cases"]}
    assert cases["CLM-1015"]["status"] == "waiting_for_sign_off"
    assert cases["CLM-1015"]["mistake_cost"] == 1350.0


def test_an_unknown_evaluation(client):
    assert read(client, "/api/evaluations/run-9").status_code == 404
    dispatch = create_dispatch(client).json()
    assert read(client, f"/api/evaluations/{dispatch['run_id']}").status_code == 404


def test_the_newest_evaluation_is_listed_first(client):
    first = create_evaluation(client).json()
    finish(client, first["run_id"])
    second = create_evaluation(client, "evaluation").json()
    listed = [e["run_id"] for e in evaluations(client)]
    assert listed == [second["run_id"], first["run_id"]]
