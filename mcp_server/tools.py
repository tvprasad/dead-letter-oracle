import json
import sys

from .models import DLQMessage, FieldError, SimulateOutput, ValidateOutput


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
