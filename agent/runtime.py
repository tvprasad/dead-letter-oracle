import asyncio
import os
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

PYTHON = sys.executable
SERVER_PARAMS = StdioServerParameters(
    command=PYTHON,
    args=["-m", "mcp_server"],
    cwd=str(Path(__file__).parent.parent),
)

_devnull = open(os.devnull, "w")


async def call_tools(tool_calls: list[tuple[str, dict]]) -> list[dict]:
    """Connect to MCP server, execute tool_calls in sequence, return results."""
    results = []
    async with stdio_client(SERVER_PARAMS, errlog=_devnull) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for tool_name, args in tool_calls:
                response = await session.call_tool(tool_name, args)
                content = response.content[0]
                results.append({"tool": tool_name, "result": content.text})
    return results


def run_tool_calls(tool_calls: list[tuple[str, dict]]) -> list[dict]:
    return asyncio.run(call_tools(tool_calls))
