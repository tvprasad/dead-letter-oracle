# ADR-007: Demo Latency and Caching

## Status
Accepted

## Context
The closed-loop reasoning path can require multiple LLM calls. Slow responses can stall the demo at the worst moment.

## Decision
Pre-cache or precompute demo-critical LLM responses for the primary scenario while preserving the visible reasoning flow.

## Rationale
Hackathon judges evaluate what they see, not whether the exact same latency would occur in production.

## Consequences
The demo must remain fast and deterministic even if APIs are slow. Live paths can still exist outside the scripted demo scenario.
