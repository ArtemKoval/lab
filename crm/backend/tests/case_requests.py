"""Requests the backend's tests send to work a case."""

from backend.tests.sign_in import DANA, signed_in


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


def sign_off(client, case_id, email=DANA):
    return client.post(f"/api/cases/{case_id}/sign-off", headers=signed_in(email))


def fail(client, case_id, reason="The model timed out"):
    return client.post(f"/api/cases/{case_id}/failure", json={"reason": reason})


def record_call(client, case_id, run_id, **usage):
    body = {"input_tokens": 1200, "output_tokens": 300, "cost": 0.0042} | usage
    return client.post(
        f"/api/cases/{case_id}/model-calls", json={"run_id": run_id, **body}
    )


def record_time(client, case_id, run_id, seconds=12.5):
    return client.post(
        f"/api/cases/{case_id}/work-times",
        json={"run_id": run_id, "seconds": seconds},
    )
