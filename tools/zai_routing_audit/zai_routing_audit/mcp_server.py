"""Thin FastMCP wrapper over the audit CLI. No logic of its own.

The burn tool is exposed in plan mode only; spending credits stays a
CLI-only action behind --spend-credits.
"""

from mcp.server.fastmcp import FastMCP

from . import cli

mcp = FastMCP("zai-routing-audit")


@mcp.tool()
def config_report(settings_path: str = "") -> dict:
    """Read back the Claude Code z.ai routing settings with the token redacted."""
    return cli.run_config(cli.namespace(settings=settings_path or None))


@mcp.tool()
def transcripts_scan(directory: str) -> dict:
    """Scan Claude Code transcript files for requested and echoed model names."""
    return cli.run_transcripts(cli.namespace(directory=directory))


@mcp.tool()
def echo_compare(names: list, max_tokens: int = 32) -> dict:
    """Send one small request per model name and compare the echoed names."""
    return cli.run_echo(cli.namespace(names=names, max_tokens=max_tokens))


@mcp.tool()
def usage_report(start: str = "", end: str = "") -> dict:
    """Read the console per-model usage rows and credit pools."""
    return cli.run_usage(cli.namespace(start=start or None, end=end or None))


@mcp.tool()
def throughput_compare(names: list, max_tokens: int = 1024) -> dict:
    """Time one bounded generation per model name."""
    return cli.run_throughput(cli.namespace(names=names, max_tokens=max_tokens))


@mcp.tool()
def burn_plan(names: list, pad_words: int = 48000) -> dict:
    """Print what a credit burn test would send, without spending credits."""
    return cli.run_burn(
        cli.namespace(names=names, pad_words=pad_words, spend_credits=False)
    )


def main():
    """Start the MCP server on stdio."""
    mcp.run()


if __name__ == "__main__":  # pragma: no cover - entry guard; main() is tested directly
    main()
