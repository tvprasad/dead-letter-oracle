from unittest.mock import MagicMock, patch

import pytest

from agent import llm

SAMPLE_MESSAGE = {
    "event": "user_created",
    "schema_version": 2,
    "payload": {"user_id": 12345, "email": "test@example.com"},
    "error": "Schema validation failed",
}

SAMPLE_VALIDATION_FAILED = {
    "valid": False,
    "errors": [{"field": "user_id", "expected_type": "string", "actual_type": "int"}],
}

SAMPLE_SIMULATION_LOW = {
    "success_likelihood": "low",
    "confidence": 0.28,
    "reason": "user_id remains integer — schema mismatch will recur on replay",
}

SAMPLE_SIMULATION_HIGH = {
    "success_likelihood": "high",
    "confidence": 0.91,
    "reason": "user_id coerced to string — schema validation should pass on replay",
}


def test_propose_initial_fix_returns_string():
    with patch("agent.llm._chat", return_value="Check schema alignment in the producer.") as mock:
        result = llm.propose_initial_fix(SAMPLE_MESSAGE, SAMPLE_VALIDATION_FAILED)
        assert isinstance(result, str)
        assert len(result) > 0
        mock.assert_called_once()


def test_revise_recommendation_returns_string():
    with patch("agent.llm._chat", return_value="Cast user_id to string at serialization.") as mock:
        result = llm.revise_recommendation("some initial fix", SAMPLE_SIMULATION_LOW)
        assert isinstance(result, str)
        assert len(result) > 0
        mock.assert_called_once()


def test_propose_initial_fix_prompt_contains_field_errors():
    captured = {}

    def capture_prompt(prompt):
        captured["prompt"] = prompt
        return "fix"

    with patch("agent.llm._chat", side_effect=capture_prompt):
        llm.propose_initial_fix(SAMPLE_MESSAGE, SAMPLE_VALIDATION_FAILED)

    assert "user_id" in captured["prompt"]
    assert "string" in captured["prompt"]


def test_revise_recommendation_prompt_signals_low_confidence():
    captured = {}

    def capture_prompt(prompt):
        captured["prompt"] = prompt
        return "revised fix"

    with patch("agent.llm._chat", side_effect=capture_prompt):
        llm.revise_recommendation("initial fix", SAMPLE_SIMULATION_LOW)

    assert "low" in captured["prompt"].lower() or "0.28" in captured["prompt"]


def test_revise_recommendation_prompt_signals_high_confidence():
    captured = {}

    def capture_prompt(prompt):
        captured["prompt"] = prompt
        return "confirmed fix"

    with patch("agent.llm._chat", side_effect=capture_prompt):
        llm.revise_recommendation("initial fix", SAMPLE_SIMULATION_HIGH)

    assert "high" in captured["prompt"].lower() or "0.91" in captured["prompt"]


def test_invalid_provider_raises():
    original_provider = llm._provider
    llm._provider = "unknown_provider"
    llm._client = None
    try:
        with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
            llm._get_client()
    finally:
        llm._provider = original_provider
        llm._client = None


def test_ollama_uses_openai_compatible_client():
    original_provider = llm._provider
    original_client = llm._client
    llm._provider = "ollama"
    llm._client = None
    try:
        mock_openai = MagicMock()
        with patch("openai.OpenAI", return_value=mock_openai) as mock_cls:
            client = llm._get_client()
            mock_cls.assert_called_once()
            call_kwargs = mock_cls.call_args.kwargs
            assert "base_url" in call_kwargs
            assert call_kwargs["api_key"] == "ollama"  # pragma: allowlist secret
            assert client is mock_openai
    finally:
        llm._provider = original_provider  # pragma: allowlist secret
        llm._client = original_client


def test_supported_providers_constant():
    assert "azure_openai" in llm.SUPPORTED_PROVIDERS
    assert "anthropic" in llm.SUPPORTED_PROVIDERS
    assert "ollama" in llm.SUPPORTED_PROVIDERS
