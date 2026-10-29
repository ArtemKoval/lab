"""The agent's tools, each named after the backend operation it calls."""

from typing import Any, Literal

import httpx
from langchain_core.tools import tool

BACKEND_URL = "http://localhost:8000"


def backend() -> httpx.Client:
    """Return a client for the CRM backend."""
    return httpx.Client(base_url=BACKEND_URL, timeout=30)


def request(
    method: str, path: str, body: dict[str, Any] | None = None
) -> httpx.Response:
    """Send one request to the backend."""
    with backend() as client:
        return client.request(method, path, json=body)


def reply(response: httpx.Response) -> str:
    """Give the model the backend's answer, or its reason for refusing."""
    if response.is_success:
        return response.text
    return f"Refused with status {response.status_code}: {response.text}"


@tool
def get_case(case_id: str) -> str:
    """Get one case in full: the story, the items claimed and the documents."""
    return reply(request("GET", f"/api/cases/{case_id}"))


@tool
def get_contract(contract_id: str) -> str:
    """Get a contract: the plan, add-ons, purchase date, trip and travelers."""
    return reply(request("GET", f"/api/contracts/{contract_id}"))


@tool
def get_case_history(customer_id: str) -> str:
    """Get a customer's earlier cases, with the outcome and the amount paid."""
    return reply(request("GET", f"/api/customers/{customer_id}/cases"))


@tool
def record_decision(
    case_id: str,
    decision: Literal["approve", "decline", "refer"],
    award: float,
    section: str,
    reason: str,
) -> str:
    """Record the decision on a case; an approval over the limit waits for sign-off."""
    body = {
        "decision": decision,
        "award": award,
        "section": section,
        "reason": reason,
    }
    return reply(request("POST", f"/api/cases/{case_id}/decision", body))


@tool
def pay_case(case_id: str, amount: float) -> str:
    """Pay an approved case its award, unless it needs a worker's sign-off."""
    return reply(request("POST", f"/api/cases/{case_id}/payment", {"amount": amount}))


TOOLS = [get_case, get_contract, get_case_history, record_decision, pay_case]
