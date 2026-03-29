# ADR-006: Demo-First Scope Constraints

## Status
Accepted

## Context
Scope creep is the biggest threat to finishing.

## Decision
Constrain the MVP to:
- one DLQ input format (JSON)
- one primary failure type (schema mismatch)
- optionally one secondary failure type
- no real Kafka/SQS integration
- no real chaos tooling
- no extra infrastructure systems

## Rationale
A narrow scope improves reliability, pace, and polish.

## Consequences
Any proposed feature that does not directly improve the core 2–3 minute demo is out of scope.
