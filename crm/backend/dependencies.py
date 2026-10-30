"""The FastAPI dependencies the backend's routers share: the database, the worker
signed in, and the senior worker an action needs."""

from collections.abc import Callable, Iterator
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Connection, select

from backend import auth
from backend.database import engine, workers
from backend.lookups import current_settings
from backend.models import Worker
from backend.money import dollars

SIGN_IN_OUT_OF_REACH = "Sign-in can't be checked: Supabase is out of reach"
NOT_SIGNED_IN = "The sign-in isn't valid. Please sign in again."


def database() -> Iterator[Connection]:
    """Open the database for one request, in a transaction committed at its end."""
    with engine().begin() as connection:
        yield connection


# Committed before the response is sent and before any background task runs.
Database = Annotated[Connection, Depends(database, scope="function")]

# Reads the access token from the Authorization header, and refuses a request
# without one with a 401.
bearer = HTTPBearer()


def signed_in_worker(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Database,
) -> Worker:
    """Return the worker signed in with the request's token, or raise a 401 when
    the token isn't valid or a 403 when no worker has its email."""
    try:
        email = auth.email_of(credentials.credentials)
    except auth.NotSignedIn as error:
        raise HTTPException(
            401, NOT_SIGNED_IN, headers={"WWW-Authenticate": "Bearer"}
        ) from error
    except auth.OutOfReach as error:
        raise HTTPException(503, SIGN_IN_OUT_OF_REACH) from error
    row = db.execute(select(workers).where(workers.c.email == email)).mappings()
    worker = row.first()
    if worker is None:
        raise HTTPException(403, f"{email} isn't one of our cases workers")
    return Worker(**worker)


SignedIn = Annotated[Worker, Depends(signed_in_worker)]


def senior(action: str) -> Callable[[Worker, Connection], Worker]:
    """Make the dependency for an action only a worker who can sign off awards
    over the limit may take: it returns the signed-in worker, or raises a 403 that
    names the action and says why."""

    def senior_worker(worker: SignedIn, db: Database) -> Worker:
        refuse_unless_senior(db, worker, action)
        return worker

    return senior_worker


def refuse_unless_senior(db: Connection, worker: Worker, action: str) -> None:
    """Raise a 403 that names the action and says why, unless the worker can sign
    off awards over the limit."""
    if not worker.can_approve_over_limit:
        limit = dollars(current_settings(db).approval_limit)
        raise HTTPException(
            403,
            f"Only a worker who can sign off awards over {limit} can {action}. "
            f"{worker.name} can't.",
        )
