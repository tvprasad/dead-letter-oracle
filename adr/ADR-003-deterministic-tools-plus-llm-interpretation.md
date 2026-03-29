# ADR-003: Deterministic Tools + LLM Interpretation

## Status
Accepted

## Context
A deterministic-only system risks making the LLM decorative. An LLM-only system risks hallucination and weak governance.

## Decision
Use deterministic tools for:
- message parsing
- schema validation
- version comparison
- replay simulation
- policy evaluation inputs

Use the LLM for:
- root-cause interpretation
- fix proposal
- recommendation refinement after validation
- human-readable explanation

## Rationale
This gives the LLM real reasoning work while preserving reliability for validation and safety-critical checks.

## Consequences
The LLM must consume structured tool outputs directly and synthesize across them.
