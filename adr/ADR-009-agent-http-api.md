# ADR-009: Agent HTTP API

## Status
Accepted

## Context
The governed incident loop (planner, LLM reasoning, gatekeeper, blackbox) had only one entry point: `main.py` as a CLI script. The MCP tools were accessible via AgentGateway, but the full pipeline was not. Any client — browser, remote agent, CI pipeline — had no way to invoke the end-to-end governed loop without spawning a subprocess.

A further concern: the initial implementation of the agent runtime bypassed AgentGateway entirely, spawning the MCP server over stdio regardless of whether the gateway was running. This made the AgentGateway integration cosmetic rather than structural.

## Decision
Two changes implemented together:

1. **`agent/api.py`** — thin FastAPI wrapper exposing `POST /run-incident`. Returns the full structured result (gatekeeper decision, BlackBox trace) as JSON. Runs on port 8000.

2. **`agent/runtime.py`** — HTTP-first transport with stdio fallback. When `AGENTGATEWAY_URL` is reachable, all tool calls route through AgentGateway (HTTP/SSE). When not reachable, the runtime falls back to stdio automatically.

## Rationale
- The agent now genuinely uses AgentGateway when it is running — the gateway is in the execution path, not just alongside it.
- The stdio fallback preserves functionality in air-gapped and local environments (same rationale as Ollama support).
- `POST /run-incident` gives any HTTP client access to the full governed pipeline without spawning a subprocess.
- FastAPI adds `/docs` (Swagger UI) automatically — useful for integration testing and demonstration.
- Separation of concerns: `planner.run_incident()` returns a structured dict. CLI and HTTP are two thin entry points over the same logic.

## Consequences
- With AgentGateway running: `POST /run-incident` → agent API → planner → gateway → MCP server. Full path visible in the AgentGateway web UI.
- Without AgentGateway: same path but tool calls go directly to MCP server over stdio. No change in behavior.
- Two independent processes: `python -m agent.api` (port 8000) and `agentgateway -f agentgateway/config.yaml` (port 3000). Each works independently.
- `AGENTGATEWAY_URL` defaults to `http://localhost:3000` and is overridable via environment variable.
