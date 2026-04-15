"""Mindcase MCP Server — exposes 30+ data collection agents as Claude tools."""

import asyncio
import json
import logging
import time

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mindcase-mcp")

mcp = FastMCP(
    "mindcase",
    instructions=(
        "Mindcase provides 30+ data collection agents for scraping structured data "
        "from LinkedIn, Instagram, Google Maps, Amazon, YouTube, and more. "
        "Use list_agents to discover available agents and get_agent_details to see "
        "required parameters before running an agent."
    ),
)

# ── SDK client (lazy singleton) ─────────────────────────────────────────────

_client = None


def _get_client():
    """Get or create the Mindcase SDK client."""
    global _client
    if _client is None:
        from mindcase.client import Mindcase

        _client = Mindcase()  # reads MINDCASE_API_KEY from env
    return _client


# ── Utility tools ───────────────────────────────────────────────────────────


@mcp.tool()
async def list_agents(group: str | None = None) -> str:
    """List all available Mindcase data collection agents.

    Args:
        group: Optional platform filter (e.g. "linkedin", "instagram", "amazon").
               If omitted, returns all agents across all platforms.
    """
    client = _get_client()
    agents = await asyncio.to_thread(client.agents.list, group)

    if not agents:
        return f"No agents found{f' for group {group!r}' if group else ''}."

    lines = []
    current_group = None
    for a in agents:
        if a.group != current_group:
            current_group = a.group
            lines.append(f"\n## {current_group}")
        lines.append(
            f"  - **{a.name}** (`{a.path}`) — "
            f"{a.description[:80]}... [{a.credits_per_row} cr/row]"
        )

    return f"**{len(agents)} agents available:**\n" + "\n".join(lines)


@mcp.tool()
async def check_credits() -> str:
    """Check remaining Mindcase credit balance."""
    try:
        client = _get_client()
        credits = await asyncio.to_thread(client.credits)
        return f"**{credits:,.1f}** credits remaining."
    except Exception as e:
        return f"Error checking credits: {e}"


@mcp.tool()
async def get_agent_details(agent_path: str) -> str:
    """Get full details and required parameters for a specific agent.

    Args:
        agent_path: Agent identifier in "group/slug" format (e.g. "instagram/profiles", "google-maps/businesses").
    """
    parts = agent_path.split("/", 1)
    if len(parts) != 2:
        return f"Invalid agent path: {agent_path!r}. Use format 'group/slug'."

    try:
        client = _get_client()
        agent = await asyncio.to_thread(client.agents.get, agent_path)
    except Exception as e:
        return f"Agent {agent_path!r} not found: {e}"

    lines = [
        f"## {agent.name}",
        f"**Path:** `{agent.group}/{agent.slug}`",
        f"**Description:** {agent.description}",
        f"**Credits:** {agent.credits_per_row} per row",
        "",
        "### Parameters:",
    ]

    for key, param in agent.parameters.items():
        req = "required" if param.required else "optional"
        line = f"  - `{key}` ({param.type}, {req}): {param.description}"
        if param.default is not None:
            line += f" [default: {param.default}]"
        lines.append(line)

    if not agent.parameters:
        lines.append("  No parameters documented.")

    return "\n".join(lines)


# ── Dynamic agent tools ────────────────────────────────────────────────────


def _format_results(results, job_id: str = "", max_rows: int = 10) -> str:
    """Format JobResults into a readable markdown table for Claude."""
    if not results.data:
        return f"**No results returned.** Job: `{job_id}`" if job_id else "**No results returned.**"

    columns = results.columns
    row_count = results.row_count

    lines = []
    if job_id:
        lines.append(f"**{row_count} rows** collected | Job: `{job_id}`")
    else:
        lines.append(f"**{row_count} rows** collected")
    lines.append("")

    show = list(results)[:max_rows]
    show_cols = columns[:6]
    lines.append("| " + " | ".join(show_cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(show_cols)) + " |")

    for row in show:
        vals = [str(row.get(c, ""))[:40] for c in show_cols]
        lines.append("| " + " | ".join(vals) + " |")

    if row_count > max_rows:
        lines.append(f"\n*Showing {max_rows} of {row_count} rows.*")

    if len(columns) > 6:
        lines.append(f"\n*Showing 6 of {len(columns)} columns: {', '.join(columns)}*")

    return "\n".join(lines)


def _make_tool_name(group: str, slug: str) -> str:
    """Convert group/slug to valid MCP tool name."""
    return f"{group}_{slug}".replace("-", "_")


def _register_agent_tool(agent) -> None:
    """Register a single agent as an MCP tool."""
    tool_name = _make_tool_name(agent.group, agent.slug)
    description = (
        f"{agent.name}: {agent.description} "
        f"[{agent.credits_per_row} credits/row]"
    )

    # Build JSON schema for tool inputs from Parameter objects
    properties = {}
    required = []

    for key, param in agent.parameters.items():
        prop: dict = {"description": param.description}

        if param.type == "array":
            prop["type"] = "array"
            prop["items"] = {"type": "string"}
        elif param.type == "integer":
            prop["type"] = "integer"
        elif param.type == "boolean":
            prop["type"] = "boolean"
        else:
            prop["type"] = "string"

        if param.options:
            prop["enum"] = [o.get("value", o) if isinstance(o, dict) else o for o in param.options]
        if param.default is not None:
            prop["default"] = param.default

        properties[key] = prop
        if param.required:
            required.append(key)

    input_schema = {
        "type": "object",
        "properties": properties,
        "required": required,
    }

    # Capture agent path in closure
    _agent_path = f"{agent.group}/{agent.slug}"

    async def _run(params: str = "{}") -> str:
        """params: JSON string of agent parameters. E.g. '{"usernames": ["nike"]}'"""
        try:
            parsed = json.loads(params) if isinstance(params, str) else params
            client = _get_client()
            # Use run_async + _wait to get both job_id and results
            job = await asyncio.to_thread(client.run_async, _agent_path, parsed)
            results = await asyncio.to_thread(
                client._wait, job.job_id, client._run_timeout, client._poll_interval
            )
            return _format_results(results, job.job_id)
        except json.JSONDecodeError:
            return f"**Error:** Invalid JSON in params: {params}"
        except Exception as e:
            return f"**Error running {_agent_path}:** {e}"

    # Register tool with FastMCP
    mcp.tool(
        name=tool_name,
        description=description
        + f"\n\nAccepts a JSON string with these parameters:\n"
        + json.dumps(input_schema["properties"], indent=2)
        + f"\nRequired: {', '.join(required) if required else 'none'}",
        annotations={"readOnlyHint": True},
    )(_run)


def _register_all_agents() -> None:
    """Fetch all agents from the API and register them as MCP tools."""
    try:
        client = _get_client()
        agent_summaries = client.agents.list()
        logger.info(f"Fetched {len(agent_summaries)} agents from API")
    except Exception as e:
        logger.error(f"Failed to fetch agents: {e}")
        return

    for i, summary in enumerate(agent_summaries):
        try:
            agent = client.agents.get(summary.path)
            _register_agent_tool(agent)
            logger.info(f"Registered tool: {_make_tool_name(agent.group, agent.slug)}")
            # Respect rate limits during registration
            if (i + 1) % 5 == 0:
                time.sleep(1)
        except Exception as e:
            logger.warning(f"Skipped {summary.path}: {e}")

    logger.info(f"MCP server ready with {len(mcp._tool_manager._tools)} tools")


# ── Startup ─────────────────────────────────────────────────────────────────

_register_all_agents()

if __name__ == "__main__":
    mcp.run()
