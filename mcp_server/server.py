from mcp.server.fastmcp import FastMCP

from . import tools

mcp = FastMCP("dead-letter-oracle")


@mcp.tool()
def dlq_read_message(file_path: str) -> dict:
    """Read a DLQ message from a local JSON file."""
    result = tools.read_message(file_path)
    return result.model_dump()


@mcp.tool()
def schema_validate(payload: dict, expected_schema: dict) -> dict:
    """Validate a message payload against an expected schema definition."""
    result = tools.validate_schema(payload, expected_schema)
    return result.model_dump()


@mcp.tool()
def replay_simulate(original_message: dict, proposed_fix: dict) -> dict:
    """Simulate replay of a message with a proposed fix. Returns confidence score."""
    result = tools.simulate_replay(original_message, proposed_fix)
    return result.model_dump()


@mcp.tool()
def agent_run_incident(file_path: str = "data/sample_dlq.json") -> dict:
    """
    Run the full governed incident loop for a DLQ message.

    Orchestrates: read -> validate -> LLM propose -> simulate -> LLM revise
    -> simulate -> gatekeeper -> blackbox trace.

    Returns a structured result with gatekeeper decision (ALLOW/WARN/BLOCK)
    and the full reasoning trace. Requires LLM credentials in environment.
    """
    return tools.run_incident(file_path)


def run():
    mcp.run(transport="stdio")
