# Governing AI Agent Decisions with MCP — Dead Letter Oracle

*How I built a governed MCP agent that analyzes failed messages, reasons through fixes, and blocks unsafe replays*

---

## The Problem Nobody Talks About

In event-driven systems, messages fail. They land in a dead-letter queue with a vague error and an angry on-call engineer staring at them.

The diagnosis is manual. The fix is a guess. The replay decision — whether to reprocess the message — is made without any confidence scoring, without governance, and without an audit trail.

That is the gap Dead Letter Oracle closes.

---

## What I Built

Dead Letter Oracle is a governed MCP agent for DLQ incident resolution. It does not just diagnose — it reasons through a fix, tests it, revises when the confidence is too low, makes a governed ALLOW/WARN/BLOCK decision, and shows you every step of its reasoning.

The full loop:

1. Read the failed DLQ message via `dlq_read_message`
2. Validate the payload via `schema_validate`
3. LLM proposes an initial fix (high-level direction)
4. `replay_simulate` tests the fix and returns a confidence score
5. If confidence is low (0.28), the LLM revises with a concrete operational fix
6. `replay_simulate` re-evaluates and returns a higher score (0.91)
7. Gatekeeper issues ALLOW / WARN / BLOCK with multi-factor reasoning
8. BlackBox renders the full 7-step reasoning trace

The deliberate first-fix failure — confidence 0.28 followed by revision to 0.91 — is the core design moment. It proves the agent reasons, not just formats.

---

## The Governance Layer

Most agent demos show a happy path. Dead Letter Oracle shows a governed path.

The Gatekeeper evaluates four independent factors before issuing a decision:

- **Schema** — is the original mismatch resolved by the proposed fix?
- **Simulation** — what is the replay confidence score?
- **Fix** — has a confirmed fix been applied?
- **Environment** — is this a production or staging system?

At 0.91 confidence in production, the decision is WARN, not ALLOW. That is intentional. The system is appropriately cautious — a human operator reviews before a live replay proceeds.

This is not a hardcoded if/else. It is multi-factor evaluation, the same pattern used in access control and fraud detection systems.

---

## Why Real MCP Over Stdio Matters

The agent and the MCP server run as separate processes communicating over stdio. The protocol boundary is real.

This matters because it means the tools are genuinely callable by any MCP-compatible client — not just this agent. The tools are a contract, not an implementation detail.

Four MCP tools — three deterministic, one orchestration:

| Tool | Type | Input | Output |
|------|------|-------|--------|
| `dlq_read_message` | Deterministic | file path | parsed DLQ message |
| `schema_validate` | Deterministic | payload, expected schema | valid/errors |
| `replay_simulate` | Deterministic | original message, proposed fix | confidence score, likelihood, reason |
| `agent_run_incident` | Orchestration | file path | gatekeeper decision + 7-step trace |

The LLM is the interpretation layer only. It proposes and revises. The deterministic tools measure and verify. The orchestration tool composes them into a governed pipeline callable from any MCP client.

---

## AgentGateway Integration

Dead Letter Oracle ships with an [AgentGateway](https://github.com/agentgateway/agentgateway) configuration that exposes all four MCP tools behind a production-grade HTTP proxy.

```bash
# Start the gateway
agentgateway -f agentgateway/config.yaml
```

The gateway adds CORS, session tracking, and a live web UI at `localhost:15000/ui`. Any client — browser, remote agent, or CI pipeline — can invoke the tools at `http://localhost:3000/` without spawning a subprocess.

The key tool is `agent_run_incident` — invoke it from the AgentGateway playground with a single input (`file_path: data/sample_dlq.json`) and get back the full governed pipeline result: both simulations, the gatekeeper decision, and the complete 7-step reasoning trace. The entire system is testable from a browser.

When AgentGateway is running, the agent runtime routes all tool calls through it via HTTP/SSE transport. When the gateway is not available, the runtime falls back to stdio automatically. The system works in both modes.

---

## Agent HTTP API

A secondary HTTP entry point is available for clients that prefer REST over MCP:

```bash
# Start the agent API
python -m agent.api

# Invoke the full governed pipeline
curl -X POST http://localhost:8000/run-incident \
  -H "Content-Type: application/json" \
  -d '{"file_path": "data/sample_dlq.json"}'
```

Swagger UI at `http://localhost:8000/docs`. Three entry points, one implementation.

---

## The BlackBox Reasoning Trace

Every run produces a structured 7-step reasoning trace:

```
[1] READ MESSAGE     event=user_created, error=Schema validation failed
[2] VALIDATE        user_id: expected string, got int
[3] PROPOSE FIX     Align producer schema — cast user_id to string at serialization
[4] SIMULATE (1)    confidence=0.28, likelihood=low
[5] REVISE FIX      Set user_id="12345" in payload before replay
[6] SIMULATE (2)    confidence=0.91, likelihood=high
[7] GOVERN          WARN — fix validated, prod environment requires manual approval
```

This trace is not a log. It is an audit record — every tool call, every LLM step, every policy trigger, in order.

---

## Three LLM Providers

The provider is switchable via a single environment variable:

| `LLM_PROVIDER` | Required vars |
|----------------|---------------|
| `azure_openai` | `AZURE_OPENAI_API_KEY`, endpoint, deployment |
| `anthropic` | `ANTHROPIC_API_KEY`, model |
| `ollama` | `OLLAMA_BASE_URL`, model |

Tested with Ollama (llama3) for local and air-gapped environments where cloud API calls are restricted.

---

## ADR-Driven Build

Every architectural decision is documented in an Architecture Decision Record before implementation. Nine ADRs covering:

- Why Dead Letter Oracle as a concept
- Real MCP with HTTP-first transport and stdio fallback
- Deterministic tools plus LLM interpretation plus orchestration tool distinction
- Gatekeeper multi-factor evaluation
- BlackBox structured reasoning trace
- Demo-first scope constraints
- Latency and caching
- AgentGateway as MCP proxy layer
- Agent HTTP API as secondary entry point

The ADRs are in the repo. They are the engineering record of every trade-off made.

---

## Production-Grade Standards

- 23 tests — unit, integration, full-pipeline (LLM mocked, no live API required)
- ruff lint and format enforced in CI
- GitHub Actions: test matrix on Python 3.12 and 3.13
- Branch protection: CI must pass, PR review required before merge
- Apache 2.0 license
- Full community standards: CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, CODEOWNERS, issue templates

---

## Try It

```bash
git clone https://github.com/tvprasad/dead-letter-oracle
cd dead-letter-oracle
pip install -r requirements.txt
cp .env.example .env
# set LLM_PROVIDER and credentials
python main.py
```

GitHub: [github.com/tvprasad/dead-letter-oracle](https://github.com/tvprasad/dead-letter-oracle)

---

*Built by Prasad Tiruveedi — [linkedin.com/in/-prasad](https://www.linkedin.com/in/-prasad/) | VPL Solutions LLC*

*Apache License 2.0*
