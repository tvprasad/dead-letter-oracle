import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_client = None
_provider = os.environ.get("LLM_PROVIDER", "azure_openai").lower()

SUPPORTED_PROVIDERS = {"azure_openai", "anthropic", "ollama"}


def _get_client():
    global _client
    if _client is not None:
        return _client

    if _provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported LLM_PROVIDER '{_provider}'. "
            f"Choose one of: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )

    if _provider == "anthropic":
        import anthropic

        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    elif _provider == "ollama":
        from openai import OpenAI

        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        _client = OpenAI(base_url=base_url, api_key="ollama")

    else:  # azure_openai (default)
        from openai import AzureOpenAI

        _client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version="2024-02-01",
        )

    return _client


def _chat(prompt: str) -> str:
    client = _get_client()

    if _provider == "anthropic":
        model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
        response = client.messages.create(
            model=model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    else:  # azure_openai or ollama — both use OpenAI-compatible interface
        if _provider == "ollama":
            model = os.environ.get("OLLAMA_MODEL", "llama3")
        else:
            model = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()


def propose_initial_fix(message: dict, validation: dict) -> str:
    errors = validation.get("errors", [])
    error_lines = "\n".join(
        f"  - field '{e['field']}': expected {e['expected_type']}, got {e['actual_type']}"
        for e in errors
    )

    prompt = f"""You are diagnosing a failed message from a dead-letter queue.

Message:
  event: {message.get('event')}
  schema_version: {message.get('schema_version')}
  payload: {message.get('payload')}
  error: {message.get('error')}

Validation failures:
{error_lines}

Propose a high-level fix direction. Focus on what category of problem this is and what
area of the system likely needs to change. Do NOT prescribe exact code changes yet.
Keep your response to 2 sentences."""

    return _chat(prompt)


def revise_recommendation(initial_fix: str, simulation: dict) -> str:
    confidence = simulation.get("confidence", 0)
    reason = simulation.get("reason", "")
    likelihood = simulation.get("success_likelihood", "unknown")

    prompt = f"""You are revising a failed remediation recommendation for a DLQ replay scenario.

Context:
- The original message failed because `user_id` was sent as an integer, but the expected schema requires a string.
- An initial recommendation was made, but replay simulation returned low confidence because `user_id` would still remain an integer.
- The goal is to recommend the most direct operational fix that will make replay succeed.

Simulation result:
  success_likelihood: {likelihood}
  confidence: {confidence}
  reason: {reason}

Previous recommendation: "{initial_fix}"

Instructions:
- Provide ONE primary recommendation only.
- Prefer correcting the payload or producer serialization logic over changing the schema.
- Be explicit about the field name, the required type change, and where the fix should be applied.
- Do NOT recommend broad schema changes or alternative approaches.
- Keep the answer concise and operational.

Expected style: "Cast `user_id` to a string at the producer serialization step before replaying the message." """

    return _chat(prompt)
