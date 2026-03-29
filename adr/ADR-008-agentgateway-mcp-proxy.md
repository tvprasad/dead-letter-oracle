# ADR-008: AgentGateway as MCP Proxy Layer

## Status
Accepted

## Context

Dead Letter Oracle exposes three MCP tools over stdio: `dlq.read_message`, `schema.validate`, and `replay.simulate`. The stdio transport is correct for local agent use (ADR-002), but it creates two gaps:

1. **Discoverability** — external clients, browser-based tools, and other agents cannot invoke the MCP tools without spawning a subprocess directly.
2. **Observability** — there is no out-of-the-box way to inspect live tool calls, routing, or session state without adding instrumentation to the server itself.

The hackathon judges evaluate Open Source Integration (40 of 100 points), with eligible projects including agentgateway, kagent, and agentregistry. AgentGateway is a Linux Foundation project specifically designed as an MCP proxy.

## Decision

Add an [AgentGateway](https://github.com/agentgateway/agentgateway) configuration at `agentgateway/config.yaml` that wraps the existing stdio MCP server behind a production-grade HTTP proxy on port 3000.

## Rationale

**AgentGateway over kagent:** Kagent requires a Kubernetes cluster and custom resource definitions. Dead Letter Oracle is a local demo-first project (ADR-006). The infrastructure overhead would contradict the demo-first constraint.

**AgentGateway over agentregistry:** AgentRegistry is a discovery/publishing layer. It adds value for teams sharing MCP servers at scale, but does not add observable, governed routing to the demo flow. AgentGateway directly enhances what judges see in a 2-minute video.

**No code changes:** The existing `python -m mcp_server` stdio entrypoint is used as-is. AgentGateway spawns it as a child process. The integration is purely configuration — zero risk to the existing implementation.

**Demo value:** AgentGateway exposes a web UI at `localhost:15000/ui` and a playground at `/ui/playground/`. Judges can invoke tools in a browser without any client code. This strengthens the Product Readiness score alongside the Open Source Integration score.

## Configuration

```yaml
binds:
  - port: 3000
    listeners:
      - routes:
          - policies:
              cors:
                allowOrigins: ["*"]
                allowHeaders: [mcp-protocol-version, content-type, cache-control]
                exposeHeaders: ["Mcp-Session-Id"]
            backends:
              - mcp:
                  targets:
                    - name: dead-letter-oracle
                      stdio:
                        cmd: python
                        args: ["-m", "mcp_server"]
```

## Consequences

- AgentGateway must be installed separately (`curl -sL https://agentgateway.dev/install | bash`)
- The core `python main.py` demo flow is unchanged — AgentGateway is an optional layer
- MCP tools are now reachable over HTTP at `http://localhost:3000/`, enabling browser and remote clients
- Live tool call inspection available at `http://localhost:15000/ui` without modifying the BlackBox

## Alternatives Considered

| Option | Rejected reason |
|--------|----------------|
| kagent | Requires Kubernetes — contradicts demo-first scope (ADR-006) |
| agentregistry | Publishing/discovery layer only, no runtime proxy or observability |
| Custom FastAPI wrapper | Re-implements what AgentGateway provides, adds maintenance burden |
| SSE transport in FastMCP | Would require code changes and breaks the stdio guarantee (ADR-002) |
