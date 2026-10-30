"""The CRM backend's API for the case agent and the agent's service: one
function for each operation they use. It has no way to the scores, the settings,
the rounds or the workers' decisions."""

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field

from agent.connection import call, get, post

DecisionKind = Literal["approve", "decline", "refer"]
APPROVE: DecisionKind = "approve"
DocumentName = Literal["wording", "manual"]
StepKind = Literal["tool_call", "tool_result", "message", "reading"]
EvaluationSet = Literal["evaluation", "held_out"]
RunKind = Literal["dispatch", "evaluation"]
DISPATCH: RunKind = "dispatch"
EVALUATION: RunKind = "evaluation"
Benefit = Literal[
    "trip_cancellation",
    "trip_interruption",
    "trip_delay",
    "baggage_delay",
    "baggage",
    "passport",
    "emergency_medical",
]


class Status(StrEnum):
    """Where a case stands."""

    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_SIGN_OFF = "waiting_for_sign_off"
    DECIDED = "decided"
    LEFT_FOR_WORKER = "left_for_worker"


LineKind = Literal[
    "item", "electronics", "cash", "expense", "hotel", "meals_without_receipts"
]


class Line(BaseModel):
    """One covered item or expense on a case."""

    description: str = Field(description="What the item or expense is")
    amount: float = Field(
        description="The total claimed for the line in US dollars, before any limits. "
        "For several items, the total for all of them"
    )
    quantity: int = Field(
        ge=1,
        description="How many separate items the line holds, such as 3 for three "
        "shirts. A pair or a set is one item, and an expense is 1",
    )
    kind: LineKind = Field(
        description="item: a belonging, or a pair or set that counts as one item. "
        "electronics: only a phone, tablet, laptop, camera or its lens, e-reader or "
        "smartwatch; any other device is an item. "
        "cash: cash that was lost or stolen. "
        "expense: any other cost with a receipt, such as a medical bill, a meal, a "
        "taxi, a fee or a prepaid trip cost. "
        "hotel: a hotel during a trip delay. "
        "meals_without_receipts: meals during a trip delay with no receipts."
    )
    nights: int = Field(
        description="For a hotel, the number of nights, and 0 otherwise"
    )
    hours: float = Field(
        description="For meals without receipts, the length of the delay in hours, "
        "and 0 otherwise"
    )


def list_cases() -> list[dict[str, Any]]:
    return get("/cases")


def get_case(case_id: str) -> dict[str, Any]:
    return get(f"/cases/{case_id}")


def get_contract(contract_id: str) -> dict[str, Any]:
    return get(f"/contracts/{contract_id}")


def get_case_history(customer_id: str) -> list[dict[str, Any]]:
    return get(f"/customers/{customer_id}/cases")


def get_version(number: int) -> dict[str, Any]:
    return get(f"/versions/{number}")


def get_current_version() -> dict[str, Any]:
    return get("/versions/current")


def search_documents(query: str) -> list[dict[str, Any]]:
    return call("GET", "/documents/search", params={"query": query})


def read_section(document: DocumentName, number: int) -> dict[str, Any]:
    return get(f"/documents/{document}/sections/{number}")


def calculate_award(
    case_id: str, benefit: Benefit, lines: list[Line], paid_by_others: float
) -> dict[str, Any]:
    body = {
        "benefit": benefit,
        "lines": [line.model_dump() for line in lines],
        "paid_by_others": paid_by_others,
    }
    return post(f"/cases/{case_id}/award", **body)


def start_case(case_id: str, thread_id: str) -> dict[str, Any]:
    return post(f"/cases/{case_id}/start", **{"thread_id": thread_id})


def record_step(case_id: str, kind: StepKind, content: str) -> dict[str, Any]:
    body = {"kind": kind, "content": content}
    return post(f"/cases/{case_id}/steps", **body)


def record_decision(
    case_id: str, decision: DecisionKind, award: float, section: str, reason: str
) -> dict[str, Any]:
    body = {
        "decision": decision,
        "award": award,
        "section": section,
        "reason": reason,
    }
    return post(f"/cases/{case_id}/decision", **body)


def pay_case(case_id: str, amount: float) -> dict[str, Any]:
    return post(f"/cases/{case_id}/payment", **{"amount": amount})


def fail_case(case_id: str, reason: str) -> dict[str, Any]:
    return post(f"/cases/{case_id}/failure", **{"reason": reason})


def record_model_call(
    case_id: str,
    run_id: str | None,
    input_tokens: int,
    output_tokens: int,
    cost: float,
) -> dict[str, Any]:
    body = {
        "run_id": run_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    }
    return post(f"/cases/{case_id}/model-calls", **body)


def record_work_time(
    case_id: str, run_id: str | None, seconds: float
) -> dict[str, Any]:
    return post(
        f"/cases/{case_id}/work-times", **{"run_id": run_id, "seconds": seconds}
    )


def create_dispatch(agents: int) -> dict[str, Any]:
    return post("/runs/dispatches", **{"agents": agents})


def create_evaluation(
    evaluation_set: EvaluationSet, tiny: bool, agents: int
) -> dict[str, Any]:
    body = {"evaluation_set": evaluation_set, "tiny": tiny, "agents": agents}
    return post("/runs/evaluations", **body)


def record_run_cases(run_id: str, case_ids: list[str]) -> dict[str, Any]:
    return call("PUT", f"/runs/{run_id}/cases", json={"case_ids": case_ids})


def finish_run(run_id: str) -> dict[str, Any]:
    return post(f"/runs/{run_id}/finish")


def stop_runs() -> list[str]:
    return post("/runs/stop")
