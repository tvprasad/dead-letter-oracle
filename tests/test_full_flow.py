from mcp_server.tools import read_message, validate_schema, simulate_replay
from governance.gatekeeper import evaluate


DLQ_FILE = "data/sample_dlq.json"

EXPECTED_SCHEMA = {
    "user_id": "string",
    "email": "string",
}

WEAK_FIX = {"payload": {"user_id": 12345, "email": "test@example.com"}}
STRONG_FIX = {"payload": {"user_id": "12345", "email": "test@example.com"}}


def test_full_reasoning_loop_deterministic():
    # Step 1: read message
    message = read_message(DLQ_FILE)
    assert message.event == "user_created"

    # Step 2: validate — expect failure
    validation = validate_schema(message.payload, EXPECTED_SCHEMA)
    assert validation.valid is False

    # Step 3: first simulation — weak fix, low confidence
    sim1 = simulate_replay(message.model_dump(), WEAK_FIX)
    assert sim1.confidence < 0.5

    # Step 4: second simulation — strong fix, high confidence
    sim2 = simulate_replay(message.model_dump(), STRONG_FIX)
    assert sim2.confidence > 0.8

    # Step 5: gatekeeper on strong fix — WARN in prod
    gate = evaluate(
        validation=validation.model_dump(),
        simulation=sim2.model_dump(),
        fix_applied=(sim2.confidence >= 0.80),
    )
    assert gate.decision == "WARN"
    assert gate.confidence == sim2.confidence
    assert len(gate.reasons) == 4


def test_simulation_confidence_gap():
    """The gap between first and second simulation must be demo-significant."""
    message = read_message(DLQ_FILE)
    sim1 = simulate_replay(message.model_dump(), WEAK_FIX)
    sim2 = simulate_replay(message.model_dump(), STRONG_FIX)
    assert (sim2.confidence - sim1.confidence) > 0.5
