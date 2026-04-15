"""CLI entry point for Mindcase."""

from __future__ import annotations

import click


@click.group()
@click.version_option(prog_name="mindcase")
def main() -> None:
    """Mindcase — 30+ data collection agents for structured web data."""
    pass


@main.command("mcp")
def mcp_command() -> None:
    """Start the Mindcase MCP server for AI-powered data collection.

    Add to Claude Code:
        claude mcp add mindcase -- mindcase mcp

    Then ask Claude to collect data from any supported platform.
    """
    from mindcase.mcp.server import mcp as mcp_server

    mcp_server.run()


if __name__ == "__main__":
    main()
