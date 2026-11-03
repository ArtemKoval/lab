"""Thin FastMCP wrapper over the dspy_gate CLI. No logic of its own.

Exposes gate status and the conformance matrix. Spending stays
CLI-only: no optimize or regen tool exists here.
"""

from mcp.server.fastmcp import FastMCP

from . import cli

SERVER_NAME = "dspy-gate"


def gate_status(repo_root: str, change_id: str) -> dict:
    """Report the gate state for one OpenSpec change."""
    code, payload = cli.cmd_status(repo_root, change_id, cli._load_modules(repo_root))
    return {"exit": code, **payload}


def conformance_matrix(repo_root: str, change_id: str) -> dict:
    """Report the conformance matrix table for one change."""
    code, payload = cli.cmd_matrix(repo_root, change_id, cli._load_modules(repo_root))
    return {"exit": code, "matrix": payload.get("matrix", "")}


def build_server():
    """Build the MCP server with the two tools registered."""
    mcp = FastMCP(SERVER_NAME)
    mcp.tool()(gate_status)
    mcp.tool()(conformance_matrix)
    return mcp


def main():
    """Start the MCP server on stdio."""
    build_server().run()


if __name__ == "__main__":  # pragma: no cover - entry guard
    main()
