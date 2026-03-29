# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Dead Letter Oracle — a conversational MCP-based agent that analyzes failed DLQ messages, explains root causes, proposes fixes, evaluates replay safety, and shows reasoning traces. Demo-first project (2-3 min live demo).

## Commands

```bash
pip install -r requirements.txt
python main.py
```

## Architecture

Four components connected via MCP over stdio:

- **MCP Server** (`mcp_server/`) — Deterministic tools: `dlq.read_message`, `schema.validate`, `schema.compare_versions`, `replay.simulate`, `policy.evaluate`. Pydantic models.
- **Agent** (`agent/`) — Planner/executor runtime. LLM is the interpretation layer, not a formatter.
- **Gatekeeper** (`governance/`) — Multi-factor policy evaluation (schema compat, replay confidence, environment, fix presence). Outputs allow/warn/block.
- **BlackBox** (`observability/`) — Structured reasoning trace: tool calls, steps, policy triggers.

## Critical demo flow

Inject malformed message -> Agent explains failure -> Proposes fix -> First fix **fails** simulation -> Agent revises -> Gatekeeper evaluates -> BlackBox shows trace.

The deliberate first-fix failure is the key moment — it proves the agent reasons.

## Build methodology

ADR-driven. Each step: attach ADR -> bounded change -> local verify -> commit. ADRs in `adr/`, phased build prompts in `prompts/`. See BUILD_SPRINT_PLAN.md for execution order.

## Constraints (from ADRs)

- Real MCP server over stdio — no mocking the protocol boundary
- Tools are deterministic; LLM handles interpretation only
- Demo data is local (`data/sample_dlq.json`) — no real Kafka
- One failure type (schema mismatch), one demo story — no scope creep
- Pre-cache LLM responses for demo reliability

## Current state

Early scaffold. Directory structure, ADRs, and sample data exist. Implementation directories (`mcp_server/`, `agent/`, `governance/`, `observability/`, `demo/`) are empty — follow BUILD_SPRINT_PLAN.md phases to implement.

## Stack

Python: fastapi, pydantic, typer, uvicorn, openai, anthropic.
