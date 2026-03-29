# ADR-009: Agent HTTP API

## Status
Accepted

## Context
The governed incident loop (planner, LLM reasoning, gatekeeper, blackbox) had only one entry point: `main.py` as a CLI script. The MCP tools were accessible via AgentGateway, but the full pipeline was not. Any client — browser, remote agent, CI pipeline — had no way to invoke the end-to-end governed loop without spawning a subprocess.

## Decision
Add `agent/api.py`: a thin FastAPI wrapper around `agent/planner.run_incident()` exposing `POST /run-incident`. The agent API runs on port 8000. AgentGateway routes `/agent/*` to it alongside the existing MCP tool proxy on port 3000.

## Rationale
- Separation of concerns: `planner.run_incident()` returns a structured dict. CLI (`run()`) and HTTP (`/run-incident`) are two thin entry points over the same logic.
- `main.py` stays as a five-line CLI entry point — not an orchestrator.
- No ADR-003 violation: the three deterministic MCP tools remain unchanged. The agent API is a separate surface, not a new MCP tool.
- The agent API runs independently on port 8000. AgentGateway continues to proxy only MCP tools (its native protocol).

## Consequences
- The full governed incident loop is now testable via HTTP without a subprocess.
- FastAPI adds `/docs` (Swagger UI) automatically — useful for integration testing.
- Two independent processes: `python -m agent.api` (port 8000) and `agentgateway -f agentgateway/config.yaml` (port 3000). Each works independently.
- AgentGateway HTTP backend routing (`http:` type) is not supported in the current release; the agent API is accessed directly on port 8000.
