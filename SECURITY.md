# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security issues by emailing **prasad@vplsolutions.com** with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within 48 hours. If the issue is confirmed, a patch will be released as soon as possible.

## Security Considerations for This Project

- **API keys**: Never commit credentials. Use `.env` (excluded by `.gitignore`). See `.env.example` for required variables.
- **LLM providers**: All LLM calls are outbound only. No user input is passed directly to tool execution — LLM output drives fix proposals, not code execution.
- **MCP tools**: All three tools (`dlq.read_message`, `schema.validate`, `replay.simulate`) are deterministic and read-only with respect to external systems.
- **Demo data**: `data/sample_dlq.json` contains synthetic data only — no real message payloads.
