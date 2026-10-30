"""The FastAPI dependencies the backend's routers share: the database, the gates on
who may call each route (the agent with its key, a signed-in worker, or either),
the worker signed in and their own sign-in, and the senior worker an action
needs."""

from collections.abc import Callable, Generator
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Connection, select

from backend import api_key, auth
from backend.database import engine, workers
from backend.lookups import current_settings
from backend.models import Worker
from backend.money import dollars

SIGN_IN_OUT_OF_REACH = "Sign-in can't be checked: Supabase is out of reach"
NOT_SIGNED_IN = "The sign-in isn't valid. Please sign in again."
NEEDS_THE_KEY = "This needs the agent's API key"
NEEDS_A_SIGN_IN_OR_THE_KEY = "Sign in, or send the agent's API key"
THE_AGENTS_REQUEST = "A request with the agent's API key is the agent's, not a worker's"
API_KEY_HEADER = "X-API-Key"
# The challenges a 401 carries, for a missing or bad sign-in or key.
BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}
API_KEY_CHALLENGE = {"WWW-Authenticate": "APIKey"}


def database() -> Generator[Connection]:
    """Open the database for one request on one connection, and commit at its end.
    A route may commit sooner, as one that asks the agent for something does first,
    so the agent sees it; what it writes afterwards is committed at the end. A
    request that fails is rolled back to its last commit."""
    with engine().connect() as connection:
        yield connection
        connection.commit()


# Committed before the response is sent.
Database = Annotated[Connection, Depends(database, scope="function")]

# Read the agent's key from its header, and a worker's access token from the
# Authorization header; a request without them is left to the gates below.
agent_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False)
optional_bearer = HTTPBearer(auto_error=False)
# Reads the access token, and refuses a request without one with a 401.
bearer = HTTPBearer()

AgentKeyHeader = Annotated[str | None, Depends(agent_key_header)]


def worker_with(token: str, db: Connection) -> Worker:
    """Return the worker signed in with a token, or raise a 401 when the token isn't
    valid or a 403 when no worker has its email."""
    try:
        email = auth.email_of(token)
    except auth.NotSignedIn as error:
        raise HTTPException(401, NOT_SIGNED_IN, headers=BEARER_CHALLENGE) from error
    except auth.OutOfReach as error:
        raise HTTPException(503, SIGN_IN_OUT_OF_REACH) from error
    row = db.execute(select(workers).where(workers.c.email == email)).mappings()
    worker = row.first()
    if worker is None:
        raise HTTPException(403, f"{email} isn't one of our case workers")
    return Worker(**worker)


def signed_in_worker(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Database,
    key: Annotated[
        str | None, Header(alias=API_KEY_HEADER, include_in_schema=False)
    ] = None,
) -> Worker:
    """Return the worker signed in with the request's token. A request that also
    carries the agent's key is the agent's, and is refused with a 403, so the key
    never stands in for a worker, whatever else the request carries. A worker's
    route doesn't offer the key in the API document."""
    worker = worker_with(credentials.credentials, db)
    if api_key.is_the_agents(key):
        raise HTTPException(403, THE_AGENTS_REQUEST)
    return worker


def sign_in_of(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    worker: Annotated[Worker, Depends(signed_in_worker)],
) -> str:
    """Return the signed-in worker's own access token, which the app passes on to
    the Copilot, so it works as the worker signed in."""
    return credentials.credentials


def the_agent(key: AgentKeyHeader) -> None:
    """Let through a request with the agent's key, and refuse any other with a 401."""
    if not api_key.is_the_agents(key):
        raise HTTPException(401, NEEDS_THE_KEY, headers=API_KEY_CHALLENGE)


def worker_or_agent(
    key: AgentKeyHeader,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(optional_bearer)
    ],
    db: Database,
) -> None:
    """Let through a request with the agent's key or a signed-in worker's token, and
    refuse one with neither with a 401."""
    if api_key.is_the_agents(key):
        return
    if credentials is None:
        raise HTTPException(401, NEEDS_A_SIGN_IN_OR_THE_KEY, headers=BEARER_CHALLENGE)
    worker_with(credentials.credentials, db)


# The gates of the routes that don't take the worker as a parameter, for a
# route's dependencies: one only the agent's side calls, one both the dashboard
# and the agent call, and one only the dashboard calls. A route that needs the
# worker takes SignedIn, or senior(action), as a parameter instead.
AgentKey = Depends(the_agent)
WorkerOrAgent = Depends(worker_or_agent)
SignedInWorker = Depends(signed_in_worker)
SignedIn = Annotated[Worker, Depends(signed_in_worker)]
# The signed-in worker's own token, for a route that passes it on to the Copilot.
SignIn = Annotated[str, Depends(sign_in_of)]


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
