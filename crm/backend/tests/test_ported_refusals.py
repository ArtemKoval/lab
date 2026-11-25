"""The refusal paths of the ported desk, resolution, and effect routes:
the guards the suites of the child repository carried, proved here against
the lab's own fixtures."""

from dataclasses import replace

from sqlalchemy import text

from backend.database import engine
from backend.tests.case_requests import held, pay, sign_off, start
from backend.tests.sign_in import DANA, MARCUS, signed_in
from domains import loader

SECTIONS = "Loan rules 2, 3 and 5"


def post_decision(client, body, worker=MARCUS, case_id="CLM-1001"):
    return client.post(
        f"/api/cases/{case_id}/worker-decision", headers=signed_in(worker), json=body
    )


def approve_body(days=14):
    return {
        "decision": "approve",
        "days": days,
        "reason": "A copy is free and the card holds two loans.",
        "section": SECTIONS,
        "benefit": "emergency_medical",
    }


def refer_body():
    return {
        "decision": "refer",
        "days": 14,
        "reason": "The title sits on the special collection shelves.",
        "section": "Loan rule 7",
        "benefit": "emergency_medical",
    }


def post_resolution(client, body, case_id="CLM-1001"):
    return client.post(
        f"/api/cases/{case_id}/resolution", headers=signed_in(DANA), json=body
    )


def loan_body(days=14):
    return {
        "resolution": "loan",
        "days": days,
        "reason": "Decided with the borrower in person.",
        "benefit": "emergency_medical",
    }


def sql(statement, **params):
    with engine().begin() as connection:
        connection.execute(text(statement), params)


def drop_items(case_id):
    sql(
        "UPDATE cases SET record = json_set(record, '$.items', json('[]')) "
        "WHERE case_id = :c",
        c=case_id,
    )


def test_an_in_progress_request_refuses_the_desk(client, agent_key):
    start(client, "CLM-1002")
    response = post_decision(client, approve_body(), case_id="CLM-1002")
    assert response.status_code == 409, response.json()
    assert "waiting" in response.json()["detail"]


def test_a_left_for_worker_request_with_a_decision_refuses_the_desk(client, agent_key):
    post_decision(client, decline_body(), case_id="CLM-1003")
    sql(
        "UPDATE cases SET status = 'left_for_worker' WHERE case_id = :c",
        c="CLM-1003",
    )
    response = post_decision(client, approve_body(), case_id="CLM-1003")
    assert response.status_code == 409, response.json()
    assert "already" in response.json()["detail"]


def test_a_decision_without_a_reason_is_refused(client, agent_key):
    body = approve_body()
    body["reason"] = "   "
    response = post_decision(client, body)
    assert response.status_code == 422, response.json()


def test_an_approval_with_no_items_is_refused(client, agent_key):
    drop_items("CLM-1001")
    response = post_decision(client, approve_body())
    assert response.status_code == 422, response.json()
    assert "loan" in response.json()["detail"]


def test_an_approval_with_an_impossible_term_is_refused(client, agent_key):
    response = post_decision(client, approve_body(days=-5))
    assert response.status_code == 422, response.json()


def test_a_resolution_of_an_evaluation_copy_is_refused(client, agent_key):
    post_decision(client, refer_body())
    sql(
        "UPDATE cases SET evaluation_id = 'EV-9' WHERE case_id = :c",
        c="CLM-1001",
    )
    response = post_resolution(client, loan_body())
    assert response.status_code == 409, response.json()
    assert "copy" in response.json()["detail"]


def test_a_resolution_with_an_impossible_term_is_refused(client, agent_key):
    post_decision(client, refer_body())
    response = post_resolution(client, loan_body(days=-5))
    assert response.status_code == 422, response.json()


def test_a_resolution_with_no_items_is_refused(client, agent_key):
    post_decision(client, refer_body())
    drop_items("CLM-1001")
    response = post_resolution(client, loan_body())
    assert response.status_code == 422, response.json()
    assert "loan" in response.json()["detail"]


def test_an_effect_refuses_an_outcome_it_does_not_run(client, agent_key):
    decided = post_decision(client, approve_body())
    assert decided.status_code == 200, decided.json()
    sql(
        "UPDATE decisions SET outcome = 'held' WHERE case_id = :c",
        c="CLM-1001",
    )
    response = pay(client, "CLM-1001")
    assert response.status_code == 409, response.json()
    assert "does not run" in response.json()["detail"]


def test_an_approval_with_an_unknown_benefit_is_refused(client, agent_key):
    body = approve_body()
    body["benefit"] = "unicorn_benefit"
    response = post_decision(client, body)
    assert response.status_code == 422, response.json()
    assert "unicorn_benefit" in response.json()["detail"]


def test_a_resolution_with_an_unknown_benefit_is_refused(client, agent_key):
    post_decision(client, refer_body())
    body = loan_body()
    body["benefit"] = "unicorn_benefit"
    response = post_resolution(client, body)
    assert response.status_code == 422, response.json()
    assert "unicorn_benefit" in response.json()["detail"]


def test_an_evaluation_copy_refuses_the_desk(client, agent_key):
    sql(
        "UPDATE cases SET evaluation_id = 'EV-9' WHERE case_id = :c",
        c="CLM-1001",
    )
    response = post_decision(client, approve_body())
    assert response.status_code == 409, response.json()
    assert "copy" in response.json()["detail"]


def a_pack_without_effects():
    """Build the replacement from the real pack BEFORE any patch lands."""
    pack = loader.pack()
    return replace(pack, manifest={**pack.manifest, "effects": {}})


def test_an_approval_for_a_pack_with_no_effect_skips_the_effect(
    client, agent_key, monkeypatch
):
    """A pack may ship an outcome with no effect declared, and the desk's
    approval then decides without running one."""
    pack = a_pack_without_effects()
    monkeypatch.setattr(loader, "pack", lambda: pack)
    decided = post_decision(client, approve_body())
    assert decided.status_code == 200, decided.json()
    case = decided.json()
    assert case["status"] == "decided"
    assert case["effect"] is None


def test_a_resolution_for_a_pack_with_no_effect_skips_the_effect(
    client, agent_key, monkeypatch
):
    pack = a_pack_without_effects()
    monkeypatch.setattr(loader, "pack", lambda: pack)
    post_decision(client, refer_body())
    response = post_resolution(client, loan_body())
    assert response.status_code == 200, response.json()
    assert response.json()["effect"] is None


def test_an_effect_run_for_a_pack_with_no_effect_refuses(
    client, agent_key, monkeypatch
):
    pack = a_pack_without_effects()
    monkeypatch.setattr(loader, "pack", lambda: pack)
    decided = post_decision(client, approve_body())
    assert decided.status_code == 200, decided.json()
    response = pay(client, "CLM-1001")
    assert response.status_code == 404, response.json()


def test_a_sign_off_for_a_pack_with_no_effect_skips_the_effect(
    client, agent_key, monkeypatch
):
    held(client, "CLM-1001", 1500.0)
    pack = a_pack_without_effects()
    monkeypatch.setattr(loader, "pack", lambda: pack)
    response = sign_off(client, "CLM-1001")
    assert response.status_code == 200, response.json()
    assert response.json()["effect"] is None


def decline_body():
    return {
        "decision": "decline",
        "days": 14,
        "reason": "Every copy of the title is on loan.",
        "section": SECTIONS,
        "benefit": "emergency_medical",
    }
