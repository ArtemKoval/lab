import pytest

from backend import main
from backend.database import effect_runs
from backend.tests.case_requests import decide, pay, record_step, sign_off, start
from backend.tests.dashboard_reads import read, steps_of
from backend.tests.rows import committed_case, count
from backend.tests.sign_in import MARCUS


def test_start_case(client):
    response = start(client, "CLM-1001")
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert response.json()["thread_id"] == "t-1"
    assert start(client, "CLM-1001").status_code == 409


def test_a_case_two_starts_both_read_as_waiting_is_started_once(client, monkeypatch):
    as_read = committed_case("CLM-1001")
    assert start(client, "CLM-1001").status_code == 200
    monkeypatch.setattr(main, "find_case", lambda db, case_id: as_read)
    second = client.post("/api/cases/CLM-1001/start", json={"thread_id": "t-2"})
    assert (second.status_code, second.json()["detail"]) == (
        409,
        "Case CLM-1001 is not waiting",
    )
    started = committed_case("CLM-1001")
    assert (started["thread_id"], started["attempts"]) == ("t-1", 1)


def test_start_needs_a_thread_id(client):
    response = client.post("/api/cases/CLM-1001/start", json={"thread_id": ""})
    assert response.status_code == 422


def test_steps(client):
    assert record_step(client, "CLM-1001", "message", "Hi").status_code == 409
    start(client, "CLM-1001")
    for kind, content in (("tool_call", "get_case"), ("tool_result", "{}")):
        assert record_step(client, "CLM-1001", kind, content).status_code == 200
    steps = steps_of(client, "CLM-1001")
    assert [(s["kind"], s["content"]) for s in steps] == [
        ("tool_call", "get_case"),
        ("tool_result", "{}"),
    ]
    assert steps[0]["step_id"] < steps[1]["step_id"]
    assert all(s["thread_id"] == "t-1" and s["created_at"] for s in steps)
    assert steps_of(client, "CLM-1002") == []
    assert read(client, "/api/cases/CLM-9999/steps").status_code == 404


MANUAL = {
    "file": "manual.md",
    "system": "Cases operations",
    "owner": "Head of cases operations",
    "reviewed": "2026-09-01",
}


def test_each_kind_of_step_is_recorded_with_its_sources(client):
    start(client, "CLM-1001")
    recorded = [
        ("screening", "No instructions found.", []),
        ("message", "Looking into it.", []),
        ("tool_call", 'read_section(document="manual", number=14)', []),
        ("tool_result", 'read_section: {"title": "Records"}', []),
        ("lookup", "Cases manual, section 14: Records", [MANUAL]),
        ("memory_search", '"earlier cases": nothing found', []),
        ("memory_save", "Case CLM-1001: A delayed flight", []),
        ("refusal", "record_decision: Refused with status 422", []),
        ("error", "RuntimeError: The model timed out", []),
    ]
    for kind, content, sources in recorded:
        response = record_step(client, "CLM-1001", kind, content, sources)
        assert response.status_code == 200
        assert response.json()["sources"] == sources
    steps = steps_of(client, "CLM-1001")
    assert [(s["kind"], s["content"], s["sources"]) for s in steps] == recorded


def test_step_kind_must_be_known_and_reading_is_gone(client):
    start(client, "CLM-1001")
    for kind in ("thought", "reading"):
        response = record_step(client, "CLM-1001", kind, "Hmm")
        assert response.status_code == 422


def test_a_step_needs_its_sources(client):
    start(client, "CLM-1001")
    body = {"kind": "message", "content": "Hi"}
    response = client.post("/api/cases/CLM-1001/steps", json=body)
    assert response.status_code == 422
    assert steps_of(client, "CLM-1001") == []


def test_decision_needs_a_case_in_progress(client):
    assert decide(client, "CLM-1001", "decline", 0).status_code == 409
    assert decide(client, "CLM-9999", "decline", 0).status_code == 404


def test_approve_and_run_the_effect_within_the_limit(client):
    start(client, "CLM-1001")
    case = decide(client, "CLM-1001", "approve", 420.0).json()
    assert case["status"] == "in_progress"
    assert case["decision"]["award"] == 420.0
    assert case["effect"] is None
    response = pay(client, "CLM-1001")
    assert response.status_code == 200
    assert response.json()["result"]["amount"] == 420.0
    assert response.json()["summary"] is None
    case = client.get("/api/cases/CLM-1001").json()
    assert case["status"] == "decided"
    assert case["effect"]["result"]["amount"] == 420.0


def test_a_repeated_decision_is_done_and_a_different_one_refused(client):
    start(client, "CLM-1001")
    first = decide(client, "CLM-1001", "approve", 420.0).json()
    again = decide(client, "CLM-1001", "approve", 420.0)
    assert again.status_code == 200
    assert again.json()["decision"] == first["decision"]
    different = decide(client, "CLM-1001", "approve", 400.0)
    assert different.status_code == 409
    assert different.json()["detail"] == "Case CLM-1001 has already been decided"
    assert decide(client, "CLM-1001", "decline", 0).status_code == 409
    pay(client, "CLM-1001")
    assert decide(client, "CLM-1001", "approve", 420.0).json()["status"] == "decided"


def test_a_repeated_effect_is_refused_with_the_recorded_run(client):
    start(client, "CLM-1001")
    decide(client, "CLM-1001", "approve", 420.0)
    pay(client, "CLM-1001")
    again = pay(client, "CLM-1001")
    assert again.status_code == 409
    assert again.json()["detail"] == "Case CLM-1001 already ran the effect 'award'"


def test_queue_shows_the_decision(client):
    start(client, "CLM-1001")
    decide(client, "CLM-1001", "approve", 420.0)
    pay(client, "CLM-1001")
    first = client.get("/api/cases").json()[0]
    assert (first["status"], first["decision"], first["award"]) == (
        "decided",
        "approve",
        420.0,
    )


def test_exactly_the_limit_needs_no_sign_off(client):
    start(client, "CLM-1002")
    decide(client, "CLM-1002", "approve", 1000.0)
    pay(client, "CLM-1002")
    assert client.get("/api/cases/CLM-1002").json()["status"] == "decided"


def test_over_the_limit_waits_for_sign_off(client):
    start(client, "CLM-1002")
    case = decide(client, "CLM-1002", "approve", 1350.0).json()
    assert case["status"] == "waiting_for_sign_off"
    response = pay(client, "CLM-1002")
    assert response.status_code == 403
    assert response.json()["detail"] == (
        "An award over $1,000.00 needs a worker's sign-off"
    )
    assert client.get("/api/cases/CLM-1002").json()["effect"] is None


def test_a_sign_off_runs_the_held_effect_once(client, agent_calls):
    start(client, "CLM-1002")
    decide(client, "CLM-1002", "approve", 1350.0)
    case = sign_off(client, "CLM-1002").json()
    assert case["status"] == "decided"
    assert case["effect"]["result"]["amount"] == 1350.0
    assert case["decision"]["signed_off_by"] == "Dana Whitfield"
    assert count(effect_runs) == 1
    assert agent_calls == [{"operation": "resume_case", "case_id": "CLM-1002"}]

    refused = pay(client, "CLM-1002")
    assert (refused.status_code, refused.json()["detail"]) == (
        409,
        "Case CLM-1002 already ran the effect 'award'",
    )
    assert sign_off(client, "CLM-1002").status_code == 409
    assert count(effect_runs) == 1
    assert client.get("/api/cases/CLM-1002").json() == case


def test_sign_off_needs_a_case_waiting_for_it(client):
    assert sign_off(client, "CLM-1001").status_code == 409
    start(client, "CLM-1001")
    decide(client, "CLM-1001", "approve", 420.0)
    assert sign_off(client, "CLM-1001").status_code == 409


def test_sign_off_needs_a_worker_who_can_approve(client, agent_calls):
    start(client, "CLM-1002")
    held = decide(client, "CLM-1002", "approve", 1350.0).json()
    response = sign_off(client, "CLM-1002", MARCUS)
    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Only a worker who can sign off awards over $1,000.00 can sign this off. "
        "Marcus Oyelaran can't."
    )
    assert client.get("/api/cases/CLM-1002").json() == held
    assert agent_calls == []


@pytest.mark.parametrize("decision", ["decline", "refer"])
def test_declines_and_referrals_are_decided_and_never_run(client, decision):
    start(client, "CLM-1003")
    case = decide(client, "CLM-1003", decision, 0).json()
    assert case["status"] == "decided"
    assert case["decision"]["decision"] == decision
    assert pay(client, "CLM-1003").status_code == 409


def test_an_effect_needs_an_approval(client):
    start(client, "CLM-1001")
    assert pay(client, "CLM-1001").status_code == 409
