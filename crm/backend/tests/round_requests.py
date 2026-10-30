"""Requests the backend's tests send to play out a round of the improver, as the
agent and the dashboard do."""

from sqlalchemy import select, update

from backend.database import engine, runs, worker_decisions
from backend.tests.case_requests import decide
from backend.tests.dashboard_reads import read
from backend.tests.rows import newest_round
from backend.tests.run_requests import get_evaluation
from backend.tests.sign_in import DANA, signed_in

# Who each worker signs in as, by their id.
EMAILS = {
    "HND-01": DANA,
    "HND-02": "marcus.oyelaran@undercover.example",
}

CHANGE = {
    "instructions": "# Working a case\n\nA rule for stolen phones.\n",
    "model": "openai/gpt-6-luna",
    "reasoning_effort": "low",
    "reason": "Two stolen phones were approved",
}
ALL = 100  # more cases than any set holds
RECIPE = {
    "recipe": "1. Read the results.\n2. Improve the recipe.\n",
    "reason": "Shorter",
}


ROUNDS = "/api/improvement/rounds"


def start_round(client, worker_id="HND-01"):
    """Start a round as a worker does, and return the start's answer."""
    return client.post(ROUNDS, headers=signed_in(EMAILS[worker_id]))


def create_round(client, worker_id="HND-01"):
    """Start a round as a worker does, which the app creates, and return it as
    the agent reads it, or the start's refusal."""
    started = start_round(client, worker_id)
    if started.status_code != 202:
        return started
    return client.get(round_path(newest_round()))


def round_path(round_id):
    return f"/api/rounds/{round_id}"


def fail_round(client, round_id, reason="RuntimeError: The improver broke"):
    """Stop a round whose work failed, as the agent does."""
    return client.post(f"{round_path(round_id)}/failure", json={"reason": reason})


def propose_change(client, round_id, **change):
    return client.post(f"{round_path(round_id)}/proposals/change", json=CHANGE | change)


def propose_recipe(client, round_id):
    return client.post(f"{round_path(round_id)}/proposals/recipe", json=RECIPE)


def review_path(round_id, proposal_id):
    return f"{ROUNDS}/{round_id}/proposals/{proposal_id}"


def approve(client, round_id, proposal_id, worker_id="HND-01"):
    """Approve a proposal as a worker does, and return the answer."""
    return client.post(
        f"{review_path(round_id, proposal_id)}/approval",
        headers=signed_in(EMAILS[worker_id]),
    )


def reject(client, round_id, proposal_id, worker_id="HND-01"):
    """Reject a proposal as a worker does, with a reason, and return the answer."""
    return client.post(
        f"{review_path(round_id, proposal_id)}/rejection",
        json={"reason": "Keep each rule general"},
        headers=signed_in(EMAILS[worker_id]),
    )


def review(client, round_id, proposal_id, verdict="approved", worker_id="HND-01"):
    """Approve or reject a proposal as a worker does on the Improvement page, and
    return it with its review as the agent reads it, or the refusal."""
    answer = approve if verdict == "approved" else reject
    reviewed = answer(client, round_id, proposal_id, worker_id)
    if reviewed.status_code != 202:
        return reviewed
    return client.get(f"{round_path(round_id)}/proposals/{proposal_id}")


def approved_change(client, round_id, **change):
    """Propose a change, approve it as Dana and make it a version under test."""
    proposal = propose_change(client, round_id, **change).json()
    review(client, round_id, proposal["proposal_id"])
    return client.post(f"{round_path(round_id)}/version").json()["number"]


def improver_call(client, round_id, cost):
    return client.post(
        f"{round_path(round_id)}/model-calls",
        json={"input_tokens": 1000, "output_tokens": 200, "cost": cost},
    )


def round_evaluation(client, round_id):
    """Ask for a round's next evaluation, on the set the backend chooses."""
    return client.post(f"/api/runs/rounds/{round_id}/evaluations")


def improvement(client):
    return read(client, "/api/improvement").json()


def stop_round(client, round_id, email=DANA):
    return client.post(f"{ROUNDS}/{round_id}/stop", headers=signed_in(email))


def into_round(round_id, *evaluations):
    """Make evaluations a round's, as if the round had run them."""
    with engine().begin() as db:
        db.execute(
            update(runs)
            .where(runs.c.run_id.in_([e["run_id"] for e in evaluations]))
            .values(round_id=round_id)
        )


def worker_reasons(evaluation_set):
    """The workers' reasons on a labeled set, by case."""
    with engine().connect() as db:
        query = select(worker_decisions).where(
            worker_decisions.c.evaluation_set == evaluation_set
        )
        return {row["case_id"]: row["reason"] for row in db.execute(query).mappings()}


def worker_answers(evaluation_set):
    """The workers' decisions and awards on a labeled set, by case."""
    with engine().connect() as db:
        query = select(worker_decisions).where(
            worker_decisions.c.evaluation_set == evaluation_set
        )
        return {
            row["case_id"]: (row["decision"], row["award"])
            for row in db.execute(query).mappings()
        }


def decide_copies(client, run, right):
    """Decide an evaluation's first copies as the workers did, as many as `right`
    says, and the rest otherwise: declining what they didn't decline, and
    referring what they declined."""
    answers = worker_answers(run["evaluation_set"])
    for n, copy in enumerate(run["cases"]):
        copy_id = copy["case_id"]
        decision, award = answers[copy_id.rsplit("-E", 1)[0]]
        if n >= right:
            decision, award = ("refer" if decision == "decline" else "decline"), 0
        client.post(f"/api/cases/{copy_id}/start", json={"thread_id": copy_id})
        decide(client, copy_id, decision, award, section="Section 3")


def play_out(client, round_id, right=0, finish=True):
    """Create one of a round's evaluations, decide its copies with `right` of them
    right, and finish it, as the agent's service would. Return the evaluation."""
    run = round_evaluation(client, round_id).json()
    decide_copies(client, run, right)
    if finish:
        client.post(f"/api/runs/{run['run_id']}/finish")
    return get_evaluation(client, run["run_id"])
