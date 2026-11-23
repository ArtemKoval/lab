"""The desk adds a case at run time: the creation route, the id series,
and the pickers. The route is pack-agnostic, so the tests run on the
default insurance pack."""

import sqlite3

from backend.tests.sign_in import DANA, signed_in

CUSTOMER = "CUS-3001"
CONTRACT = "POL-2001"


def a_request(
    customer=CUSTOMER,
    contract=CONTRACT,
    summary="Flight home canceled by the airline",
    story=(
        "Maya Patel's flight home from Rome was canceled"
        " and she rebooked for the next morning."
    ),
    items=None,
):
    return {
        "customer_id": customer,
        "contract_id": contract,
        "case_type": "trip_delay",
        "summary": summary,
        "story": story,
        "incident_location": "Rome, Italy",
        "incident_date": "2026-11-23",
        "submitted_on": "2026-11-23",
        "documents": [],
        "items": items
        if items is not None
        else [
            {
                "description": "Airport hotel, one night",
                "category": "accommodation",
                "amount": 245.0,
            },
        ],
    }


def test_created_request_lands_in_the_queue_as_waiting(dashboard):
    reply = dashboard.post("/api/cases", json=a_request(), headers=signed_in(DANA))
    assert reply.status_code == 200, reply.json()
    case = reply.json()
    assert case["case_id"] == "CLM-1902"
    assert case["status"] == "waiting"
    queue = dashboard.get("/api/cases", headers=signed_in(DANA)).json()
    queue_ids = {c["case_id"] for c in queue}
    assert case["case_id"] in queue_ids


def test_unknown_customer_is_refused(dashboard):
    reply = dashboard.post(
        "/api/cases", json=a_request(customer="CUS-none"), headers=signed_in(DANA)
    )
    assert reply.status_code == 404
    queue = dashboard.get("/api/cases", headers=signed_in(DANA)).json()
    assert len(queue) == 26


def test_unknown_contract_is_refused(dashboard):
    reply = dashboard.post(
        "/api/cases", json=a_request(contract="POL-none"), headers=signed_in(DANA)
    )
    assert reply.status_code == 404


def test_empty_summary_is_refused(dashboard):
    reply = dashboard.post(
        "/api/cases", json=a_request(summary="   "), headers=signed_in(DANA)
    )
    assert reply.status_code == 422


def test_empty_items_are_refused(dashboard):
    reply = dashboard.post(
        "/api/cases", json=a_request(items=[]), headers=signed_in(DANA)
    )
    assert reply.status_code == 422


def test_the_id_series_skips_past_the_seed(dashboard):
    ids = [
        dashboard.post("/api/cases", json=a_request(), headers=signed_in(DANA)).json()[
            "case_id"
        ]
        for _ in range(3)
    ]
    assert ids == ["CLM-1902", "CLM-1903", "CLM-1904"]


def test_an_evaluation_copy_does_not_move_the_series(database, dashboard):
    db = sqlite3.connect(database)
    db.execute(
        "insert into cases values"
        " ('CLM-1901-E7','CUS-3001','{}','waiting',null,0,null,null,null)"
    )
    db.commit()
    reply = dashboard.post("/api/cases", json=a_request(), headers=signed_in(DANA))
    assert reply.json()["case_id"] == "CLM-1902"


def test_the_first_case_in_an_empty_database(database, dashboard):
    db = sqlite3.connect(database)
    db.execute("delete from cases")
    db.commit()
    reply = dashboard.post("/api/cases", json=a_request(), headers=signed_in(DANA))
    assert reply.status_code == 200, reply.json()
    assert reply.json()["case_id"] == "C-1"


def test_the_customer_search_returns_every_customer_without_a_query(dashboard):
    reply = dashboard.get("/api/customers", headers=signed_in(DANA))
    assert reply.status_code == 200
    found = {c["customer_id"] for c in reply.json()}
    assert "CUS-3001" in found
    assert "CUS-3014" in found


def test_the_customer_search_keeps_the_named_match(dashboard):
    reply = dashboard.get(
        "/api/customers/find", params={"name": "Patel"}, headers=signed_in(DANA)
    )
    names = [c["name"] for c in reply.json()]
    assert names
    assert all("Patel" in n for n in names)


def test_contracts_filter_by_customer(dashboard):
    reply = dashboard.get("/api/customers/CUS-3001/contracts", headers=signed_in(DANA))
    assert reply.status_code == 200
    assert [c["contract_id"] for c in reply.json()] == ["POL-2001"]


def test_contracts_refuse_an_unknown_customer(dashboard):
    reply = dashboard.get("/api/customers/CUS-none/contracts", headers=signed_in(DANA))
    assert reply.status_code == 404
