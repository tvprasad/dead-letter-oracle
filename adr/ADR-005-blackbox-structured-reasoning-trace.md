# ADR-005: BlackBox Structured Reasoning Trace

## Status
Accepted

## Context
Raw logs are unreadable in a 2-minute demo. Judges want to understand what the agent did and why.

## Decision
Implement BlackBox as a structured, human-readable reasoning trace showing:
- tool calls
- findings
- policy triggers
- recommendation evolution
- final decision

## Rationale
This gives the project a memorable explainability moment and strengthens trust.

## Consequences
BlackBox output must be demo-friendly, concise, and readable at a glance.
