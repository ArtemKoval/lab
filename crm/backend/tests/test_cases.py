from sqlalchemy import select

from backend import seed
from backend.database import engine, worker_decisions
from backend.tests.run_requests import create_evaluation, finish, queue


def test_list_cases(client):
    cases = client.get("/api/cases").json()
    assert len(cases) == 26
    assert [case["case_id"] for case in cases] == sorted(
        case["case_id"] for case in cases
    )
    assert {case["status"] for case in cases} == {"waiting"}
    assert cases[0] == {
        "case_id": "CLM-1001",
        "customer_name": "Maya Patel",
        "case_type": "trip_delay",
        "summary": "Flight home canceled by the airline, rebooked the next morning",
        "amount_claimed": 420.0,
        "submitted_on": "2026-06-24",
        "status": "waiting",
        "decision": None,
        "award": None,
        "resuming": False,
    }


def test_get_case(client):
    case = client.get("/api/cases/CLM-1001").json()
    assert case["customer_name"] == "Maya Patel"
    assert case["story"].startswith("My flight home from Rome")
    assert len(case["items"]) == 3
    assert len(case["documents"]) == 4
    assert case["status"] == "waiting"
    assert case["decision"] is None
    assert case["payment"] is None


def test_get_contract(client):
    contract = client.get("/api/contracts/POL-2001").json()
    assert contract["plan"] == "premium"
    assert contract["add_ons"] == []
    assert contract["trip"]["destination"] == "Rome, Italy"
    assert contract["trip"]["returns_on"] == "2026-06-18"


def test_get_case_history_leaves_out_personal_details(client):
    response = client.get("/api/customers/CUS-3001/cases")
    history = response.json()
    assert [case["case_id"] for case in history] == ["CLM-0412"]
    for field in ("email", "phone", "address", "date_of_birth"):
        assert field not in response.text


def test_unknown_ids(client):
    for path in (
        "/api/cases/CLM-9999",
        "/api/contracts/POL-9999",
        "/api/customers/CUS-9999/cases",
    ):
        response = client.get(path)
        assert response.status_code == 404
        assert "9999 not found" in response.json()["detail"]


def test_seed_command(capsys):
    seed.main()
    assert capsys.readouterr().out == (
        "Seeded 26 cases, 51 contracts, 50 customers and 3 workers "
        "into crm.db, with 25 held-out cases and 50 workers' decisions "
        "for evaluations, and version 1 of the configuration and of the recipe\n"
    )


def test_the_security_teams_case_waits_in_the_queue(client):
    case = client.get("/api/cases/CLM-1901").json()
    assert (case["status"], case["contract_id"], case["customer_id"]) == (
        "waiting",
        "POL-2901",
        "CUS-3901",
    )
    assert client.get("/api/contracts/POL-2901").status_code == 200
    assert client.get("/api/customers/CUS-3901/cases").status_code == 200
    [listed] = [c for c in queue(client) if c["case_id"] == "CLM-1901"]
    assert listed["customer_name"] == "Derek Vance"


def test_the_security_teams_case_is_in_neither_evaluation_set(client):
    with engine().connect() as db:
        query = select(worker_decisions.c.case_id)
        assert "CLM-1901" not in set(db.execute(query).scalars())
    for evaluation_set in ("evaluation", "held_out"):
        for tiny in (True, False):
            run = create_evaluation(client, evaluation_set, tiny).json()
            copied = [case["case_id"] for case in run["cases"]]
            assert copied
            assert not [c for c in copied if c.startswith("CLM-1901")]
            finish(client, run["run_id"])
