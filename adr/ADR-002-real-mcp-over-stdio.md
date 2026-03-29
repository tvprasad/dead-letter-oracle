# ADR-002: Real MCP Over Stdio

## Status
Accepted

## Context
A custom tool registry built on top of plain function calls provides no protocol guarantee. The boundary between agent and tools would be an implementation detail, not a contract.

## Decision
Implement a **real MCP server** over **stdio transport** and a true MCP client that invokes tools across the protocol boundary.

## Rationale
This makes MCP:
- real
- visible
- defensible
- category-aligned

Stdio is the simplest transport that satisfies the real protocol boundary requirement without additional infrastructure.

## Consequences
All tools must be callable through the MCP interface, not by direct in-process calls.
