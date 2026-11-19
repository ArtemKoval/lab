"""The lead's resolution of a referred request: the loan issued through the
pack's effect, or the decline recorded as the case's decision."""

from backend.tests.case_requests import decide, record_decision, start
from backend.tests.sign_in import DANA, MARCUS, signed_in

REFERRAL = {"decision": "refer", "section": "Section 9, Special Items"}


def a_referred_case(client):
    start(client, "CLM-1001")
    response = record_decision(client, "CLM-1001", **REFERRAL)
    assert response.status_code == 200, response.json()


def test_the_lead_issues_the_award(client, agent_key):
    a_referred_case(client)
    response = client.post(
        "/api/cases/CLM-1001/resolution",
        headers=signed_in(DANA),
        json={
            "resolution": "loan",
            "days": 14,
            "reason": "In person.",
            "benefit": "emergency_medical",
        },
    )
    assert response.status_code == 200, response.json()
    case = response.json()
    assert case["status"] == "decided"
    assert case["decision"]["outcome"] == "award"
    assert case["effect"]["summary"]
    assert case["effect"]["summary"] == "195.00 awarded"


def test_the_lead_declines_in_her_words(client, agent_key):
    a_referred_case(client)
    response = client.post(
        "/api/cases/CLM-1001/resolution",
        headers=signed_in(DANA),
        json={
            "resolution": "decline",
            "days": 14,
            "reason": "The title stays in the building.",
            "benefit": "loan",
        },
    )
    assert response.status_code == 200, response.json()
    decision = response.json()["decision"]
    assert decision["decision"] == "decline"
    assert decision["decided_by"] == "Dana Whitfield"
    assert decision["reason"] == "The title stays in the building."


def test_the_desk_librarian_cannot_resolve(client, agent_key):
    a_referred_case(client)
    response = client.post(
        "/api/cases/CLM-1001/resolution",
        headers=signed_in(MARCUS),
        json={
            "resolution": "loan",
            "days": 14,
            "reason": "In person.",
            "benefit": "emergency_medical",
        },
    )
    assert response.status_code == 403
    assert "resolve a referred request" in response.json()["detail"]


def test_only_a_referral_resolves(client, agent_key):
    start(client, "CLM-1001")
    decide(client, "CLM-1001", "decline", 0)
    response = client.post(
        "/api/cases/CLM-1001/resolution",
        headers=signed_in(DANA),
        json={
            "resolution": "loan",
            "days": 14,
            "reason": "In person.",
            "benefit": "emergency_medical",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Only a referred request resolves this way"


def test_the_effect_runs_once(client, agent_key):
    a_referred_case(client)
    body = {
        "resolution": "loan",
        "days": 14,
        "reason": "In person.",
        "benefit": "emergency_medical",
    }
    headers = signed_in(DANA)
    first = client.post("/api/cases/CLM-1001/resolution", headers=headers, json=body)
    assert first.status_code == 200
    second = client.post("/api/cases/CLM-1001/resolution", headers=headers, json=body)
    assert second.status_code == 409
