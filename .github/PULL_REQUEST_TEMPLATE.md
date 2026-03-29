## Summary
<!-- What does this PR do? 1-3 bullet points -->
-

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Refactor
- [ ] Documentation
- [ ] CI / tooling

## ADR Impact
<!-- Does this change require a new ADR or amend an existing one? -->
- [ ] No ADR impact
- [ ] Covered by ADR: <!-- ADR-00X -->
- [ ] New ADR required: <!-- ADR-00X draft in adr/ -->

## Test Plan
- [ ] `python -m pytest tests/ -v` — all passing
- [ ] `python -m ruff check .` — no lint errors
- [ ] New tests added for new behavior
- [ ] LLM calls mocked — no live API credentials in tests

## Checklist
- [ ] Deterministic tools remain deterministic (ADR-003)
- [ ] No hardcoded credentials or endpoints
- [ ] `.env.example` updated if new env vars added
