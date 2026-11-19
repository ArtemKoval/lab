"""The desk's decisions on a waiting request: approve with a term, decline,
or refer to the lead, all as the signed-in worker."""

from backend.tests.sign_in import DANA, MARCUS, signed_in

SECTIONS = "Loan rules 2, 3 and 5"


def post_decision(client, body, worker=DANA, case_id="CLM-1001"):
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


def decline_body():
    return {
        "decision": "decline",
        "days": 14,
        "reason": "Every copy of the title is on loan.",
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


def test_the_desk_approves_at_the_base_term(client, agent_key):
    response = post_decision(client, approve_body(), worker=MARCUS)
    assert response.status_code == 200, response.json()
    case = response.json()
    assert case["status"] == "decided"
    assert case["decision"]["decision"] == "approve"
    assert case["decision"]["decided_by"] == "Marcus Oyelaran"
    assert case["decision"]["outcome"] == "award"
    assert case["effect"]["summary"]


def test_the_desk_approval_over_the_limit_holds_for_the_lead(client, agent_key):
    """CLM-1011's request resolves to 1500, over the 1000 limit, so
    the desk's approval holds for the lead's sign-off and no effect has
    run."""
    body = approve_body(14)
    body["benefit"] = "baggage"
    response = post_decision(client, body, case_id="CLM-1011")
    assert response.status_code == 200, response.json()
    case = response.json()
    assert case["status"] == "waiting_for_sign_off"
    assert case["effect"] is None


def test_the_desk_declines_in_her_words(client, agent_key):
    response = post_decision(client, decline_body(), worker=MARCUS)
    assert response.status_code == 200, response.json()
    decision = response.json()["decision"]
    assert decision["decision"] == "decline"
    assert decision["decided_by"] == "Marcus Oyelaran"


def test_the_desk_refers_to_the_lead(client, agent_key):
    response = post_decision(client, refer_body(), worker=MARCUS)
    assert response.status_code == 200, response.json()
    decision = response.json()["decision"]
    assert decision["decision"] == "refer"


def test_the_lead_resolves_what_the_desk_referred(client, agent_key):
    post_decision(client, refer_body())
    response = client.post(
        "/api/cases/CLM-1001/resolution",
        headers=signed_in(DANA),
        json={
            "resolution": "loan",
            "days": 14,
            "reason": "Decided with the borrower in person.",
            "benefit": "emergency_medical",
        },
    )
    assert response.status_code == 200, response.json()
    assert response.json()["effect"]["summary"].endswith("awarded")


def test_a_decided_request_refuses_the_desk(client, agent_key):
    post_decision(client, decline_body())
    response = post_decision(client, approve_body())
    assert response.status_code == 409


def test_a_body_without_sections_is_refused(client, agent_key):
    body = approve_body()
    body["section"] = "   "
    response = post_decision(client, body)
    assert response.status_code == 422
