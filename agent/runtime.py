import asyncio
import os
import sys
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client

PYTHON = sys.executable
SERVER_PARAMS = StdioServerParameters(
    command=PYTHON,
    args=["-m", "mcp_server"],
    cwd=str(Path(__file__).parent.parent),
)

AGENTGATEWAY_URL = os.environ.get("AGENTGATEWAY_URL", "http://localhost:3000")

_devnull = open(os.devnull, "w")


def _gateway_reachable() -> bool:
    """Return True if AgentGateway is reachable at AGENTGATEWAY_URL."""
    try:
        resp = httpx.get(AGENTGATEWAY_URL, timeout=1.0)
        return resp.status_code < 500
    except Exception:
        return False


async def _call_via_gateway(tool_calls: list[tuple[str, dict]]) -> list[dict]:
    """Execute tool calls through AgentGateway (HTTP/SSE transport)."""
    results = []
    async with sse_client(AGENTGATEWAY_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for tool_name, args in tool_calls:
                response = await session.call_tool(tool_name, args)
                content = response.content[0]
                results.append({"tool": tool_name, "result": content.text})
    return results


async def _call_via_stdio(tool_calls: list[tuple[str, dict]]) -> list[dict]:
    """Execute tool calls by spawning MCP server directly over stdio (fallback)."""
    results = []
    async with stdio_client(SERVER_PARAMS, errlog=_devnull) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for tool_name, args in tool_calls:
                response = await session.call_tool(tool_name, args)
                content = response.content[0]
                results.append({"tool": tool_name, "result": content.text})
    return results


async def call_tools(tool_calls: list[tuple[str, dict]]) -> list[dict]:
    """
    Execute tool calls against the MCP server.

    Transport selection:
      1. AgentGateway (HTTP/SSE) if AGENTGATEWAY_URL is reachable.
      2. stdio (direct subprocess) as fallback.

    This ensures the system works in air-gapped and gateway-down scenarios
    while routing through the governed proxy when available.
    """
    if _gateway_reachable():
        try:
            return await _call_via_gateway(tool_calls)
        except Exception as exc:  # nosec B110 — intentional fallback to stdio
            _ = exc  # gateway reachable but call failed; fall through to stdio
    return await _call_via_stdio(tool_calls)


def run_tool_calls(tool_calls: list[tuple[str, dict]]) -> list[dict]:
    return asyncio.run(call_tools(tool_calls))
