"""Requests the backend's tests send to work a case."""


def start(client, case_id):
    return client.post(f"/api/cases/{case_id}/start", json={"thread_id": "t-1"})


def decide(client, case_id, decision, award):
    return client.post(
        f"/api/cases/{case_id}/decision",
        json={
            "decision": decision,
            "award": award,
            "section": "Section 3, Trip Delay",
            "reason": "The delay was covered.",
        },
    )


def pay(client, case_id, amount):
    return client.post(f"/api/cases/{case_id}/payment", json={"amount": amount})


def sign_off(client, case_id, worker_id):
    return client.post(f"/api/cases/{case_id}/sign-off", json={"worker_id": worker_id})


def fail(client, case_id, reason="The model timed out"):
    return client.post(f"/api/cases/{case_id}/failure", json={"reason": reason})
