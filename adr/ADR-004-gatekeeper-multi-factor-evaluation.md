# ADR-004: Gatekeeper Multi-Factor Evaluation

## Status
Accepted

## Context
A simple allow/block branch looks trivial and weak in judging.

## Decision
Implement Gatekeeper as a multi-factor evaluator using:
- schema compatibility
- replay simulation result
- environment
- confidence score
- fix presence / resolution status

## Rationale
This makes governance look and behave like evaluation rather than a hardcoded if-statement.

## Consequences
Gatekeeper outputs must include:
- decision
- risk/confidence context
- readable reasoning
