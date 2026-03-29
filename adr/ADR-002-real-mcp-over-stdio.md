# ADR-002: Real MCP Over Stdio

## Status
Accepted

## Context
“MCP-style” abstractions were judged as insufficiently defensible in Q&A. A custom tool registry risks looking like function-calling dressed up as protocol.

## Decision
Implement a **real MCP server** over **stdio transport** and a true MCP client that invokes tools across the protocol boundary.

## Rationale
This makes MCP:
- real
- visible
- defensible
- category-aligned

Stdio is the simplest credible transport for hackathon scope.

## Consequences
All tools exposed in the demo must be callable through the MCP interface, not by direct in-process calls.
