# ADR-002: Real MCP Over Stdio With HTTP Gateway Fallback

## Status
Accepted (updated — see transport selection below)

## Context
A custom tool registry built on top of plain function calls provides no protocol guarantee. The boundary between agent and tools would be an implementation detail, not a contract.

## Decision
Implement a **real MCP server** with a two-tier transport strategy:

1. **HTTP/SSE via AgentGateway** (preferred) — agent routes tool calls through the gateway at `AGENTGATEWAY_URL` when reachable.
2. **stdio** (fallback) — agent spawns the MCP server as a direct subprocess when the gateway is not available.

Transport selection is automatic at runtime. No code change required to switch.

## Rationale
- The MCP protocol boundary is real in both paths — tools are never called in-process.
- Routing through AgentGateway when available places the governed proxy in the execution path, enabling session tracking, CORS, and live observability in the web UI.
- The stdio fallback preserves functionality in air-gapped and local environments where a gateway process is not running — consistent with the Ollama support rationale (ADR-001).
- A system that fails completely when a proxy is down is not production-grade.

## Consequences
- `agent/runtime.py` probes `AGENTGATEWAY_URL` (default: `http://localhost:3000`) before each tool call batch.
- If the gateway is reachable, all tool calls flow through it. If not, stdio is used transparently.
- All tools remain callable through the MCP interface in both transports — no direct in-process calls.
- `AGENTGATEWAY_URL` is configurable via environment variable.
