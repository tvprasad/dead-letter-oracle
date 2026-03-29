# ADR-005: BlackBox Structured Reasoning Trace

## Status
Accepted

## Context
Raw logs expose implementation noise — tool call parameters, serialization details, timestamps — without surfacing the reasoning chain. Operators need to understand what the agent decided and why, not how the runtime executed it.

## Decision
Implement BlackBox as a structured, human-readable reasoning trace showing:
- tool calls
- findings
- policy triggers
- recommendation evolution
- final decision

## Rationale
Structured output makes the agent's reasoning auditable and verifiable without reading raw logs.

## Consequences
BlackBox output must be concise and human-readable without additional tooling.
