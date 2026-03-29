# ADR-003: Deterministic Tools + LLM Interpretation

## Status
Accepted (updated — orchestration tool added, see below)

## Context
A deterministic-only system risks making the LLM decorative. An LLM-only system risks hallucination and weak governance.

## Decision
Two categories of MCP tools:

**Deterministic tools** — no LLM, no side effects, same input always produces same output:
- `dlq_read_message` — message parsing
- `schema_validate` — schema validation
- `replay_simulate` — confidence scoring

**Orchestration tool** — composes the deterministic tools with LLM interpretation and governance:
- `agent_run_incident` — invokes the full governed pipeline in-process, calls deterministic tool functions directly (no circular MCP dependency), returns structured result with gatekeeper decision and BlackBox trace

## Rationale
- Deterministic tools give the LLM real, verifiable inputs to reason over.
- The orchestration tool exposes the full governed pipeline through the same MCP surface — one protocol, one port, all capabilities.
- Calling deterministic tool functions directly inside `agent_run_incident` avoids a circular MCP dependency while preserving the single-surface architecture.
- The LLM remains the interpretation layer only — it proposes and revises. The deterministic tools measure and verify.

## Consequences
- The 3 deterministic tools are independently callable with no LLM credentials required.
- `agent_run_incident` requires LLM credentials (`LLM_PROVIDER` and provider vars) in the MCP server process environment.
- All 4 tools are accessible via AgentGateway at port 3000.
