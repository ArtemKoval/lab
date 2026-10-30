"""The backend's operations on customers, for the Copilot: finding them by name, and
one customer with their contracts and cases, without their contact details or date
of birth."""

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from backend.database import case_view, cases, customers, contracts
from backend.dependencies import Database, SignedInWorker
from backend.lookups import customer_record
from backend.models import Customer, CustomerMatch, Contract, PreviousCase
from backend.views import to_summary

router = APIRouter()

# A name to look for, with something in it besides spaces.
Name = Annotated[str, Query(pattern=r"\S", description="Words in the customer's name")]


@router.get(
    "/api/customers", operation_id="find_customers", dependencies=[SignedInWorker]
)
def find_customers(name: Name, db: Database) -> list[CustomerMatch]:
    """Find the customers whose name holds every word given, ignoring case."""
    query = select(customers.c.customer_id, customers.c.name)
    for word in name.lower().split():
        query = query.where(
            func.lower(customers.c.name).contains(word, autoescape=True)
        )
    rows = db.execute(query.order_by(customers.c.name)).mappings()
    return [CustomerMatch(**row) for row in rows]


@router.get(
    "/api/customers/{customer_id}",
    operation_id="get_customer",
    dependencies=[SignedInWorker],
)
def get_customer(customer_id: str, db: Database) -> Customer:
    """Get a customer with their contracts, earlier cases and cases in our queue."""
    record = customer_record(db, customer_id)
    theirs = select(contracts.c.record).where(
        contracts.c.record["customer_id"].as_string() == customer_id
    )
    their_contracts = [Contract(**contract) for contract in db.execute(theirs).scalars()]
    in_the_queue = case_view.where(
        cases.c.customer_id == customer_id, cases.c.evaluation_id.is_(None)
    ).order_by(cases.c.case_id)
    return Customer(
        customer_id=customer_id,
        name=record["name"],
        customer_since=record["customer_since"],
        contracts=their_contracts,
        earlier_cases=[PreviousCase(**c) for c in record["previous_cases"]],
        cases_in_the_queue=[
            to_summary(row) for row in db.execute(in_the_queue).mappings()
        ],
    )
