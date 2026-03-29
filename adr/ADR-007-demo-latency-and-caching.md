# ADR-007: Demo Latency and Caching

## Status
Accepted

## Context
The closed-loop reasoning path can require multiple LLM calls. Slow responses can stall the demo at the worst moment.

## Decision
Pre-cache or precompute demo-critical LLM responses for the primary scenario while preserving the visible reasoning flow.

## Rationale
Pre-caching the primary scenario eliminates API latency as a variable during live execution while keeping the reasoning flow intact and visible.

## Consequences
The demo must remain fast and deterministic even if APIs are slow. Live paths can still exist outside the scripted demo scenario.
