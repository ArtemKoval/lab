"""Serve the context layer on the laptop, at http://127.0.0.1:8006/mcp:
uv run -m context

CRM_CONTEXT_HOST names the interface to bind, for a run whose port the web
reaches: CRM_CONTEXT_HOST=0.0.0.0 uv run -m context"""

import os

from context.server import build_server

if __name__ == "__main__":
    build_server(host=os.environ.get("CRM_CONTEXT_HOST", "127.0.0.1")).run(
        transport="streamable-http"
    )
