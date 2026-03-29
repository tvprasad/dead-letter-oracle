# Dead Letter Oracle

**Governed MCP Agent for DLQ Incident Resolution**

[![CI](https://github.com/tvprasad/dead-letter-oracle/actions/workflows/ci.yml/badge.svg)](https://github.com/tvprasad/dead-letter-oracle/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE-2.0.txt)
[![Release](https://img.shields.io/github/v/release/tvprasad/dead-letter-oracle)](https://github.com/tvprasad/dead-letter-oracle/releases)
[![MCP](https://img.shields.io/badge/protocol-MCP%20stdio-purple)](https://modelcontextprotocol.io)
[![AgentGateway](https://img.shields.io/badge/gateway-AgentGateway-blue)](https://github.com/agentgateway/agentgateway)
[![LLM](https://img.shields.io/badge/LLM-Azure%20OpenAI%20%7C%20Anthropic%20%7C%20Ollama-orange)](https://github.com/tvprasad/dead-letter-oracle#llm-provider)

![Dead Letter Oracle](docs/poster.png)

Dead Letter Oracle is an MCP-based agent that analyzes failed dead-letter queue messages, explains root causes, proposes and simulates fixes, and makes governed replay decisions, with a full reasoning trace.

---

## Problem

In event-driven systems, failed messages require manual debugging:

- Root cause is unclear from the error alone
- Schema mismatches are hard to diagnose without tooling
- Replay decisions are made without confidence scoring or governance

---

## Solution

Dead Letter Oracle automates the full incident loop:

1. Reads the failed DLQ message via `dlq.read_message`
2. Validates the payload via `schema.validate`
3. LLM proposes an initial fix (high-level direction)
4. `replay.simulate` tests the fix and returns a confidence score
5. If confidence is low, LLM revises with a concrete, operational fix
6. `replay.simulate` re-evaluates the revised fix
7. Gatekeeper issues ALLOW / WARN / BLOCK with multi-factor reasoning
8. BlackBox renders the full 7-step reasoning trace

---

## Architecture

```
                        AgentGateway (port 3000)
                        └── MCP Proxy ── CORS, session, web UI
                                │
User → CLI → Agent Runtime      │
                ├── MCP Client ─┘ stdio ── MCP Server
                │                              ├── dlq.read_message
                │                              ├── schema.validate
                │                              └── replay.simulate
                ├── LLM  (propose → simulate → revise)
                ├── Gatekeeper  (ALLOW / WARN / BLOCK)
                └── BlackBox    (reasoning trace)
```

The MCP protocol boundary is real. The agent and server run as separate processes communicating over stdio. Tools are deterministic. The LLM is the interpretation layer only.

---

## Running with AgentGateway

Dead Letter Oracle ships with an [AgentGateway](https://github.com/agentgateway/agentgateway) configuration that exposes both the MCP tools and the governed agent API behind a single proxy with built-in CORS, session tracking, and a live web UI.

Two backends are unified under one gateway:

- **MCP tools** (deterministic, protocol-level) — `dlq_read_message`, `schema_validate`, `replay_simulate`
- **Agent API** (full governed loop) — `POST /agent/run-incident` returns the complete 7-step reasoning trace and gatekeeper decision as JSON

```bash
# Install agentgateway (Linux/macOS)
curl -sL https://agentgateway.dev/install | bash

# Windows: download binary from https://github.com/agentgateway/agentgateway/releases
# then run:
agentgateway-windows-amd64.exe -f agentgateway/config.yaml

# Start the agent API (port 8000)
python -m agent.api

# Start the gateway (from repo root, Linux/macOS)
agentgateway -f agentgateway/config.yaml
```

| Endpoint | URL |
|----------|-----|
| MCP proxy | http://localhost:3000/ |
| Agent API | http://localhost:3000/agent/run-incident |
| Agent docs | http://localhost:8000/docs |
| Web UI | http://localhost:15000/ui |
| Playground | http://localhost:15000/ui/playground/ |

Open the Playground, connect to `http://localhost:3000/`, and invoke `dlq_read_message`, `schema_validate`, or `replay_simulate` directly from the browser. To test the full governed pipeline, `POST /agent/run-incident` with `{"file_path": "data/sample_dlq.json"}`.

The gateway config is at [`agentgateway/config.yaml`](agentgateway/config.yaml).

---

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in LLM credentials (see .env.example)
python main.py
```

### LLM Provider

Set `LLM_PROVIDER` in `.env`:

| Value | Required vars |
|-------|--------------|
| `azure_openai` (default) | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` |
| `anthropic` | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` |
| `ollama` | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |

> Tested with Ollama (llama3) for local and air-gapped deployment, relevant for enterprise and federal environments where cloud API calls are restricted.

### Running tests

```bash
python -m pytest tests/ -v
```

---

## MCP Tools

| Tool | Input | Output |
|------|-------|--------|
| `dlq.read_message` | `file_path` | Parsed DLQ message |
| `schema.validate` | `payload`, `expected_schema` | `valid`, `errors[]` |
| `replay.simulate` | `original_message`, `proposed_fix` | `confidence`, `success_likelihood`, `reason` |

---

## Gatekeeper Factors

Multi-factor evaluation, not a simple if/else:

- **Schema** — mismatch detected / resolved
- **Simulation** — confidence score from `replay.simulate`
- **Fix** — whether a confirmed fix was applied
- **Environment** — prod requires higher confidence threshold

---

## Project Structure

```
mcp_server/      MCP server + tools (deterministic)
agent/           Agent runtime, planner, LLM integration, HTTP API
governance/      Gatekeeper — multi-factor replay evaluation
observability/   BlackBox — structured reasoning trace
agentgateway/    AgentGateway config (MCP proxy + agent API, web UI, playground)
data/            Sample DLQ message (local, no Kafka)
adr/             Architecture Decision Records (ADR-001 through ADR-008)
tests/           22 unit + integration tests
docs/            Architecture poster (poster.png)
```

---

## Hackathon Context

Developed during the AI Hackathon submission period (Feb 2 – Apr 3, 2026).

Built ADR-first: each phase locked decisions before implementation. The deliberate first-fix failure (confidence 0.28 → 0.91) is the core demo moment. It proves the agent reasons, not just formats.

---

## Author

**Prasad Tiruveedi** — [linkedin.com/in/-prasad](https://www.linkedin.com/in/-prasad/) | VPL Solutions LLC

---

## Acknowledgements

**Design review:** Venkat, Satish, and Vijaya — feedback on system positioning and poster design.

**Development approach:** Built using an agent team orchestrated by a human architect — each tool assigned a distinct role, mirroring the multi-component design of the system itself.

**AI tools used during development:**
- Claude Code — implementation, architecture, and testing
- ChatGPT — ideation, prompt refinement, and poster generation
- Gemini — ideation and design feedback
- GitHub Copilot — ideation and testing
- Ollama (llama3) — local LLM validation and air-gap testing

## License

Apache License 2.0 — see [LICENSE-2.0.txt](LICENSE-2.0.txt)
