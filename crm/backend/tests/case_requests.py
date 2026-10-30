"""Requests the backend's tests send to work a case."""

from backend.tests.rows import calculated
from backend.tests.sign_in import DANA, signed_in

# Who makes the decisions the tests record, as the case agent says it.
MAKER = "CRM Agent, version 1"


def start(client, case_id):
    return client.post(f"/api/cases/{case_id}/start", json={"thread_id": "t-1"})


def record_step(client, case_id, kind, content, sources=()):
    """Record a step as the agent does, with the context files a lookup came from,
    and none for any other step."""
    body = {"kind": kind, "content": content, "sources": list(sources)}
    return client.post(f"/api/cases/{case_id}/steps", json=body)


def line(description, amount, kind="item", **extra):
    """A line of a award request: one item, with no nights or hours, unless given."""
    return {
        "description": description,
        "amount": amount,
        "kind": kind,
        "quantity": 1,
        "nights": 0,
        "hours": 0,
    } | extra


def work_out_award(client, case_id, benefit, lines, paid_by_others=0):
    body = {"benefit": benefit, "lines": lines, "paid_by_others": paid_by_others}
    return client.post(f"/api/cases/{case_id}/award", json=body)


def record_decision(client, case_id, **changes):
    """Ask to record a decision as the case agent does, with its maker: a referral
    unless told otherwise."""
    body = {
        "decision": "refer",
        "award": 0,
        "section": "Section 3, Trip Delay",
        "reason": "The delay was covered.",
        "decided_by": MAKER,
    } | changes
    return client.post(f"/api/cases/{case_id}/decision", json=body)


def decide(client, case_id, decision, award, section="Section 3, Trip Delay"):
    """Record a decision as the case agent does, an approval with a calculation of
    the same award kept for the case's attempt first."""
    if decision == "approve":
        calculated(case_id, award)
    return record_decision(
        client, case_id, decision=decision, award=award, section=section
    )


def held(client, case_id, award):
    """Start a case and approve it over the limit, which holds it for sign-off,
    and return it."""
    start(client, case_id)
    return decide(client, case_id, "approve", award).json()


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


# Why the Gateway refuses a payment in the tests.
GATEWAY_REFUSAL = "Tool Execution Denied: the Contract forbids it"


def hold(client, case_id, reason=GATEWAY_REFUSAL):
    return client.post(f"/api/cases/{case_id}/hold", json={"reason": reason})


# A senior worker's note on a decision they send back, in the tests.
NOTE = "Meridian Air has already paid $350 for the lost bag; take it off the award."


def send_back(client, case_id, note=NOTE, email=DANA):
    return client.post(
        f"/api/cases/{case_id}/send-back",
        json={"note": note},
        headers=signed_in(email),
    )


def take(client, case_id, run_id=None):
    """Take a sent-back case, as a dispatch does with its run or a resume with
    none."""
    return client.post(f"/api/cases/{case_id}/take", json={"run_id": run_id})


def record_heartbeat(client, case_id):
    return client.post(f"/api/cases/{case_id}/heartbeat")
