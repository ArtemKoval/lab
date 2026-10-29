from backend import seed


def test_list_cases(client):
    cases = client.get("/api/cases").json()
    assert len(cases) == 25
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
        "Seeded 25 cases, 50 contracts, 49 customers and 3 workers into crm.db\n"
    )
