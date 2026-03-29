# Contributing to Dead Letter Oracle

Thank you for your interest in contributing. This project is an MCP-based governed agent for DLQ incident resolution — contributions that maintain the ADR-driven architecture and production-grade standards are welcome.

## Before You Start

Read the ADRs in `adr/` — they document every major design decision. Changes that contradict an existing ADR require a new ADR first.

## Development Setup

```bash
git clone https://github.com/tvprasad/dead-letter-oracle.git
cd dead-letter-oracle
pip install -r requirements.txt
cp .env.example .env
# fill in LLM credentials
python -m pytest tests/ -v
```

## How to Contribute

### Reporting Bugs

Open an issue using the **Bug Report** template. Include:
- Python version and OS
- `LLM_PROVIDER` setting (no API keys)
- Full error output
- Steps to reproduce

### Suggesting Features

Open an issue using the **Feature Request** template. Reference the relevant ADR if applicable. New capabilities that change the agent architecture should propose a new ADR.

### Submitting a Pull Request

1. Fork the repository and create a branch from `main`
2. Make your changes — keep scope tight (one concern per PR)
3. Ensure all tests pass: `python -m pytest tests/ -v`
4. Ensure lint passes: `python -m ruff check .`
5. Add tests for any new behavior
6. Open a PR against `main` with a clear description

## Code Standards

- **Style**: ruff (import sort + format) — run `python -m ruff check . --fix` before committing
- **Types**: Pydantic models for all tool inputs/outputs (see `mcp_server/models.py`)
- **Tests**: mock LLM calls; never require live API credentials in tests
- **Determinism**: MCP tools must remain deterministic — LLM is the interpretation layer only (ADR-003)
- **No scope creep**: one failure type, one demo story (ADR-006)

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
