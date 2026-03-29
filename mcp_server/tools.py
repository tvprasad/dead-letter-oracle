import json
import sys

from .models import DLQMessage, FieldError, SimulateOutput, ValidateOutput

EXPECTED_SCHEMA = {
    "user_id": "string",
    "email": "string",
}

WEAK_FIX_PAYLOAD = {
    "user_id": 12345,  # still an int — simulation will flag this
    "email": "test@example.com",
}
STRONG_FIX_PAYLOAD = {
    "user_id": "12345",  # coerced to string — simulation passes
    "email": "test@example.com",
}


def read_message(file_path: str) -> DLQMessage:
    print("[ MCP ] Tool invoked: dlq.read_message", flush=True, file=sys.stderr)
    with open(file_path, "r") as f:
        data = json.load(f)
    return DLQMessage(**data)


def validate_schema(payload: dict, expected_schema: dict) -> ValidateOutput:
    print("[ MCP ] Tool invoked: schema.validate", flush=True, file=sys.stderr)
    errors: list[FieldError] = []

    for field, expected_type in expected_schema.items():
        if field not in payload:
            errors.append(
                FieldError(
                    field=field,
                    expected_type=expected_type,
                    actual_type="missing",
                )
            )
            continue

        actual = payload[field]
        type_map: dict[str, type | tuple[type, ...]] = {
            "string": str,
            "number": (int, float),
            "object": dict,
            "boolean": bool,
        }
        expected_py = type_map.get(expected_type)

        if expected_py and not isinstance(actual, expected_py):
            errors.append(
                FieldError(
                    field=field,
                    expected_type=expected_type,
                    actual_type=type(actual).__name__,
                )
            )

    return ValidateOutput(valid=len(errors) == 0, errors=errors)


def simulate_replay(original_message: dict, proposed_fix: dict) -> SimulateOutput:
    print("[ MCP ] Tool invoked: replay.simulate", flush=True, file=sys.stderr)

    fix_payload = proposed_fix.get("payload", {})
    user_id = fix_payload.get("user_id")

    # Strong fix: user_id is now a string
    if isinstance(user_id, str):
        return SimulateOutput(
            success_likelihood="high",
            confidence=0.91,
            reason="user_id coerced to string — schema validation should pass on replay",
        )

    # Partial fix: user_id still an integer
    if isinstance(user_id, int):
        return SimulateOutput(
            success_likelihood="low",
            confidence=0.28,
            reason="user_id remains integer — schema mismatch will recur on replay",
        )

    # No payload fix at all
    return SimulateOutput(
        success_likelihood="low",
        confidence=0.15,
        reason="proposed fix does not modify the payload — root cause unaddressed",
    )


def run_incident(file_path: str = "data/sample_dlq.json") -> dict:
    """
    Full governed incident loop. Calls tool functions directly (in-process)
    to avoid circular MCP dependency. The 3 deterministic tools remain
    independently callable via MCP; this function composes them.

    Requires LLM credentials in environment (LLM_PROVIDER + provider vars).
    """
    print("[ MCP ] Tool invoked: agent.run_incident", flush=True, file=sys.stderr)

    # Import here to keep LLM deps out of the deterministic tool path
    from agent import llm
    from governance.gatekeeper import evaluate as gatekeeper_evaluate
    from observability.blackbox import BlackBox

    trace = BlackBox()

    # Step 1: read
    message = read_message(file_path)
    trace.record(
        "Read message from DLQ",
        f"event={message.event} schema_version={message.schema_version}",
    )

    # Step 2: validate
    validation = validate_schema(message.payload, EXPECTED_SCHEMA)
    field_errors = validation.errors
    if field_errors:
        e = field_errors[0]
        trace.record(
            "Detected schema mismatch",
            f"'{e.field}' expected {e.expected_type}, got {e.actual_type}",
        )
    else:
        trace.record("Schema validation passed")

    # Step 3: LLM proposes initial fix
    initial_fix = llm.propose_initial_fix(message.model_dump(), validation.model_dump())
    trace.record("Proposed initial fix", _truncate(initial_fix, 80))

    # Step 4: simulate weak fix
    sim1 = simulate_replay(message.model_dump(), {"payload": WEAK_FIX_PAYLOAD})
    trace.record(
        f"Simulation result: {sim1.success_likelihood} confidence ({sim1.confidence})",
        sim1.reason,
    )

    # Step 5: LLM revises
    revised_fix = llm.revise_recommendation(initial_fix, sim1.model_dump())
    trace.record("Revised fix after low-confidence simulation", _truncate(revised_fix, 80))

    # Step 6: simulate strong fix
    sim2 = simulate_replay(message.model_dump(), {"payload": STRONG_FIX_PAYLOAD})
    trace.record(
        f"Re-simulation result: {sim2.success_likelihood} confidence ({sim2.confidence})",
        sim2.reason,
    )

    # Step 7: gatekeeper
    gate = gatekeeper_evaluate(
        validation=validation.model_dump(),
        simulation=sim2.model_dump(),
        fix_applied=(sim2.confidence >= 0.80),
    )
    trace.record(
        f"Gatekeeper decision: {gate.decision}",
        f"confidence={gate.confidence} | {gate.reasons[0]}",
    )

    return {
        "message": message.model_dump(),
        "validation": validation.model_dump(),
        "initial_fix": initial_fix,
        "simulation1": sim1.model_dump(),
        "revised_fix": revised_fix,
        "simulation2": sim2.model_dump(),
        "gatekeeper": {
            "decision": gate.decision,
            "confidence": gate.confidence,
            "reasons": gate.reasons,
        },
        "trace": trace.entries(),
    }


def _truncate(text: str, max_len: int) -> str:
    text = text.replace("\n", " ")
    return text[:max_len] + "..." if len(text) > max_len else text
