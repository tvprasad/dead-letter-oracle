# ADR-009: Agent HTTP API (Secondary Entry Point)

## Status
Accepted

## Context
The governed incident loop is exposed as `agent_run_incident` MCP tool via AgentGateway (ADR-003). A secondary HTTP entry point (`POST /run-incident`) is provided for clients that prefer REST over MCP protocol.

## Decision
`agent/api.py` — thin FastAPI wrapper on port 8000. Delegates directly to `mcp_server/tools.run_incident()`, the same function backing the MCP tool. No duplicate logic.

## Rationale
- MCP is the primary surface. The Agent API is a convenience layer for HTTP clients (curl, browsers, CI pipelines) that do not speak MCP.
- Both surfaces call the same underlying function — behavior is identical regardless of entry point.
- FastAPI adds `/docs` (Swagger UI) automatically, useful for integration testing.

## Consequences
- Three entry points, one implementation: AgentGateway MCP tool, HTTP API, CLI (`python main.py`).
- LLM credentials required in environment for all three.
- `agent/api.py` is optional infrastructure — the system is complete without it.
