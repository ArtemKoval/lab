"""AgentCore Memory, the agent's notes on each customer: the store a case graph
keeps them in when CRM_MEMORY_ID is set, what it saves of a decided case,
and a search of one customer's memories."""

import os
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.store.base import BaseStore
from langgraph_checkpoint_aws import AgentCoreMemoryStore

MEMORY_ID = "CRM_MEMORY_ID"
# Every memory of a customer is under /customers/<customer>, and the summary of
# each of their cases under /customers/<customer>/cases/<case>/.
CUSTOMERS = "customers"
CASE_SUMMARY = f"/{CUSTOMERS}/{{customer_id}}/cases/{{case_id}}/"
MOST_FOUND = 5
# What AgentCore Memory raises when it can't be reached or refuses a call.
UNREACHABLE = (BotoCoreError, ClientError)


def memory_store() -> BaseStore | None:
    """AgentCore Memory at CRM_MEMORY_ID, read now, in the AWS CLI's region,
    or None when it isn't set."""
    memory_id = os.getenv(MEMORY_ID)
    if not memory_id:
        return None
    region = boto3.Session().region_name
    return AgentCoreMemoryStore(memory_id=memory_id, region_name=region)


def what_was_claimed(case: dict[str, Any]) -> str:
    """The case as its customer made it: its summary, the benefit claimed, the
    date and place of the incident and the items claimed, and never the story or
    the documents."""
    items = "; ".join(
        f"{i['description']}, ${i['amount']:,.2f}" for i in case["items"]
    )
    return (
        f"Case {case['case_id']}: {case['summary']}\n"
        f"Benefit claimed: {case['case_type']}\n"
        f"Incident: {case['incident_date']}, {case['incident_location']}\n"
        f"Items claimed: {items}"
    )


def what_was_decided(case: dict[str, Any]) -> str:
    """The decision on a case, with its award, section and reason."""
    decision = case["decision"]
    return (
        f"Decision on {case['case_id']}: {decision['decision']}, paying "
        f"${decision['award']:,.2f}, under {decision['section']}. "
        f"{decision['reason']}"
    )


def remember(store: BaseStore, case: dict[str, Any]) -> str:
    """Save a decided case to memory, with its customer as the actor and the case
    as the session: the case as the customer's message and the decision as the
    agent's. Return what was saved."""
    actor_and_session = (case["customer_id"], case["case_id"])
    claimed, decided = what_was_claimed(case), what_was_decided(case)
    store.put(actor_and_session, "case", {"message": HumanMessage(claimed)})
    store.put(actor_and_session, "decision", {"message": AIMessage(decided)})
    return f"{claimed}\n{decided}"


def recall(store: BaseStore, customer_id: str, case_id: str, query: str) -> list[str]:
    """Search one customer's memories and return each one's text, leaving out the
    summary of the case being worked on. AgentCoreMemoryStore gives every result
    the prefix searched as its namespace, so a memory's own namespaces are read
    from its value."""
    own = CASE_SUMMARY.format(customer_id=customer_id, case_id=case_id)
    found = store.search((CUSTOMERS, customer_id), query=query, limit=MOST_FOUND)
    return [
        item.value["content"] for item in found if own not in item.value["namespaces"]
    ]
