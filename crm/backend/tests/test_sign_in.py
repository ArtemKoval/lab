"""Workers sign in through Supabase Auth, and the backend checks the worker on
every action a worker takes."""

import jwt
import pytest
from sqlalchemy import select

from backend import auth
from backend.database import engine, load, metadata, workers
from backend.tests.case_requests import decide, start
from backend.tests.gates import WORKER_OPERATIONS
from backend.tests.sign_in import AUTH_URL, DANA, OTHER_KEY, signed_in

NOT_SIGNED_IN = {
    "no token": {},
    "another key": signed_in(DANA, key=OTHER_KEY),
    "expired": signed_in(DANA, expires_in=-60),
    "another audience": signed_in(DANA, audience="anon"),
    "not a token": {"Authorization": "Bearer not-a-token"},
}


def everything_recorded():
    """Every row of every table, to show that a request changed nothing."""
    with engine().connect() as db:
        return {
            table.name: [dict(row) for row in db.execute(select(table)).mappings()]
            for table in metadata.sorted_tables
        }


def test_the_signed_in_worker(client):
    response = client.get("/api/me", headers=signed_in(DANA))
    assert response.status_code == 200
    assert response.json() == {
        "worker_id": "HND-01",
        "name": "Dana Whitfield",
        "role": "Senior Claims Handler",
        "email": DANA,
        "can_approve_over_limit": True,
    }


def test_a_sign_in_issued_a_little_ahead_of_our_clock_is_fine(client):
    headers = signed_in(DANA, issued_in=5)
    assert client.get("/api/me", headers=headers).status_code == 200


def test_an_out_of_reach_auth_service_isnt_a_bad_sign_in(client, monkeypatch):
    def unreachable(_):
        raise jwt.PyJWKClientConnectionError("Fail to fetch data from the url")

    monkeypatch.setattr(jwt.PyJWKClient, "fetch_data", unreachable)
    refused = client.get("/api/me", headers=signed_in(DANA))
    assert (refused.status_code, refused.json()["detail"]) == (
        503,
        "Sign-in can't be checked: Supabase is out of reach",
    )


def test_a_sign_in_that_isnt_a_workers_is_refused(client):
    response = client.get("/api/me", headers=signed_in("visitor@example.com"))
    assert response.status_code == 403
    assert response.json()["detail"] == (
        "visitor@example.com isn't one of our cases workers"
    )


@pytest.mark.parametrize(
    ("method", "path", "body"),
    WORKER_OPERATIONS.values(),
    ids=WORKER_OPERATIONS.keys(),
)
def test_every_worker_operation_needs_a_sign_in_and_the_key_wont_do(
    client, agent_calls, method, path, body
):
    """The client sends the agent's key with every request, which never stands in
    for a worker."""
    start(client, "CLM-1002")
    decide(client, "CLM-1002", "approve", 1350.0)
    before = everything_recorded()
    for headers in NOT_SIGNED_IN.values():
        response = client.request(method, path, json=body, headers=headers)
        assert response.status_code == 401
    assert everything_recorded() == before
    assert agent_calls == []


def test_seeding_stores_each_workers_email_and_who_can_sign_off_over_the_limit():
    with engine().connect() as db:
        rows = db.execute(select(workers).order_by(workers.c.worker_id))
        seeded = [
            (row["name"], row["email"], row["can_approve_over_limit"])
            for row in rows.mappings()
        ]
    assert seeded == [
        (h["name"], h["email"], h["can_approve_over_limit"])
        for h in load("workers.json")
    ]
    assert [can for _, _, can in seeded] == [True, False, False]


def test_the_public_keys_are_fetched_from_the_supabase_project():
    keys = auth.public_keys()
    assert keys.uri == f"{AUTH_URL}/jwks.json"
    assert auth.public_keys() is keys
