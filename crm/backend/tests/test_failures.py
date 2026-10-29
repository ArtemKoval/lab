from backend.tests.case_requests import decide, fail, start


def test_starting_a_case_counts_the_attempt(client):
    assert client.get("/api/cases/CLM-1004").json()["attempts"] == 0
    assert start(client, "CLM-1004").json()["attempts"] == 1


def test_a_failed_attempt_goes_back_in_the_queue(client):
    start(client, "CLM-1004")
    case = fail(client, "CLM-1004").json()
    assert (case["status"], case["attempts"]) == ("waiting", 1)
    last = client.get("/api/cases/CLM-1004/steps").json()[-1]
    assert (last["kind"], last["content"]) == ("error", "The model timed out")
    assert last["thread_id"] == "t-1"


def test_a_second_failure_leaves_the_case_for_a_worker(client):
    start(client, "CLM-1004")
    fail(client, "CLM-1004")
    start(client, "CLM-1004")
    case = fail(client, "CLM-1004", "The agent went round in circles").json()
    assert (case["status"], case["attempts"]) == ("left_for_worker", 2)
    assert start(client, "CLM-1004").status_code == 409
    assert decide(client, "CLM-1004", "decline", 0).status_code == 409
    queue = {c["case_id"]: c for c in client.get("/api/cases").json()}
    assert queue["CLM-1004"]["status"] == "left_for_worker"
    errors = [
        s["content"]
        for s in client.get("/api/cases/CLM-1004/steps").json()
        if s["kind"] == "error"
    ]
    assert errors == ["The model timed out", "The agent went round in circles"]


def test_failure_needs_a_case_in_progress(client):
    assert fail(client, "CLM-1001").status_code == 409
    start(client, "CLM-1001")
    decide(client, "CLM-1001", "approve", 420.0)
    assert fail(client, "CLM-1001").status_code == 409
    start(client, "CLM-1002")
    decide(client, "CLM-1002", "approve", 1350.0)
    assert fail(client, "CLM-1002").status_code == 409
    assert client.get("/api/cases/CLM-1002").json()["status"] == (
        "waiting_for_sign_off"
    )
    assert client.get("/api/cases/CLM-1001/steps").json() == []
    assert fail(client, "CLM-9999").status_code == 404


def test_failure_needs_a_reason(client):
    start(client, "CLM-1001")
    assert fail(client, "CLM-1001", "").status_code == 422
    assert client.get("/api/cases/CLM-1001").json()["status"] == "in_progress"
