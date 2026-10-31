"""The case agent's own API document: the OpenAPI document of the reads, the
resolution tools, and the effect executor, which the Gateway turns into tools."""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute, iter_route_contexts

from domains import loader

# The reads and the resolution tools every pack serves, plus the executor of
# every effect the pack declares.
BASE_OPERATIONS = {
    "get_case",
    "get_contract",
    "get_case_history",
    "resolve_outcome",
    "record_decision",
}


def operations() -> set[str]:
    """The operations the document serves: the base set, plus the generic
    executor of every effect the pack declares."""
    served = set(BASE_OPERATIONS)
    if loader.pack().effects:
        served.add("run_effect")
    return served


def document(app: FastAPI) -> dict[str, Any]:
    """Build the document of the case agent's operations from the app's own routes,
    with no servers, which the deployment adds, and no security schemes, which a
    Gateway's OpenAPI target doesn't support: its credential provider sends the
    key instead."""
    routes = [
        context
        for context in iter_route_contexts(app.routes)
        if isinstance(context.route, APIRoute)
        and context.route.operation_id in operations()
    ]
    agents = get_openapi(
        title=f"{app.title} case agent", version=app.version, routes=routes
    )
    del agents["components"]["securitySchemes"]
    for path in agents["paths"].values():
        for operation in path.values():
            del operation["security"]
    return agents
