"""What the app gives the Copilot to read beside the dashboard's reads: customers by
name and in full, the count of awards over the limit, a run a worker started, and
the Copilot's model."""

import json

from backend.tests.case_requests import held, sign_off
from backend.tests.dashboard_reads import read
from backend.tests.run_requests import create_evaluation, start_dispatch
from backend.tests.sign_in import DANA


def test_find_customers_by_the_words_in_their_name(dashboard):
    found = read(dashboard, "/api/customers?name=maya").json()
    assert found == [{"customer_id": "CUS-3001", "name": "Maya Patel"}]
    assert read(dashboard, "/api/customers?name=PATEL%20maya").json() == found
    assert read(dashboard, "/api/customers?name=nobody").json() == []


def test_a_blank_name_finds_nothing(dashboard):
    for name in ("", "%20%20"):
        assert read(dashboard, f"/api/customers?name={name}").status_code == 422
    assert read(dashboard, "/api/customers").status_code == 422


def test_a_customer_in_full_without_their_personal_details(dashboard):
    customer = read(dashboard, "/api/customers/CUS-3001").json()
    assert customer["name"] == "Maya Patel"
    assert "POL-2001" in [contract["contract_id"] for contract in customer["contracts"]]
    assert "CLM-0412" in [case["case_id"] for case in customer["earlier_cases"]]
    assert "CLM-1001" in [c["case_id"] for c in customer["cases_in_the_queue"]]
    assert {"email", "phone", "address", "date_of_birth"} & set(customer) == set()
    assert "maya.patel@example.com" not in json.dumps(customer)
    unknown = read(dashboard, "/api/customers/CUS-9999")
    assert (unknown.status_code, unknown.json()["detail"]) == (
        404,
        "Customer CUS-9999 not found",
    )


def sign_offs(client):
    return read(client, "/api/sign-offs").json()


def test_the_held_approvals_and_those_signed_off(client, dashboard):
    assert sign_offs(dashboard) == {"held": 0, "signed_off": 0}
    held(client, "CLM-1002", 1350.0)
    sign_off(client, "CLM-1002", DANA)
    assert sign_offs(dashboard) == {"held": 1, "signed_off": 1}
    held(client, "CLM-1008", 1200.0)
    assert sign_offs(dashboard) == {"held": 2, "signed_off": 1}


def test_a_held_approval_on_a_copy_isnt_counted(client, dashboard):
    copy = create_evaluation(client).json()["cases"][0]["case_id"]
    held(client, copy, 1500.0)
    assert sign_offs(dashboard) == {"held": 0, "signed_off": 0}


def test_a_worker_reads_the_run_a_start_names(dashboard):
    started = start_dispatch(dashboard, 10, DANA)
    assert started.status_code == 202
    body = started.json()
    run = read(dashboard, f"/api/runs/{body['run_id']}").json()
    assert (run["number"], run["agents"], run["status"]) == (
        body["number"],
        10,
        "running",
    )


def test_the_copilots_model(dashboard, monkeypatch):
    model = read(dashboard, "/api/copilot/model").json()
    assert model == {"model": "openai/gpt-6-luna", "reasoning_effort": "low"}
    monkeypatch.setenv("MODEL_NAME", "free/model")
    model = read(dashboard, "/api/copilot/model").json()
    assert model == {"model": "free/model", "reasoning_effort": "default"}
