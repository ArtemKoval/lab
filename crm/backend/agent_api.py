"""The case agent's own API document: the OpenAPI document of the six operations
its tools and its payment call, which the Gateway turns into tools."""

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute, iter_route_contexts

OPERATIONS = {
    "get_case",
    "get_contract",
    "get_case_history",
    "calculate_award",
    "record_decision",
    "pay_case",
}


def document(app: FastAPI) -> dict[str, Any]:
    """Build the document of the case agent's operations from the app's own routes,
    with no servers, which the deployment adds, and no security schemes, which a
    Gateway's OpenAPI target doesn't support: its credential provider sends the
    key instead."""
    routes = [
        context
        for context in iter_route_contexts(app.routes)
        if isinstance(context.route, APIRoute)
        and context.route.operation_id in OPERATIONS
    ]
    agents = get_openapi(
        title=f"{app.title} case agent", version=app.version, routes=routes
    )
    del agents["components"]["securitySchemes"]
    for operations in agents["paths"].values():
        for operation in operations.values():
            del operation["security"]
    return agents
