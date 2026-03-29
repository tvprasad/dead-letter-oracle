from mcp_server.tools import read_message, validate_schema, simulate_replay


DLQ_FILE = "data/sample_dlq.json"

EXPECTED_SCHEMA = {
    "user_id": "string",
    "email": "string",
}


def test_read_message_returns_correct_event():
    msg = read_message(DLQ_FILE)
    assert msg.event == "user_created"
    assert msg.schema_version == 2
    assert "user_id" in msg.payload
    assert "email" in msg.payload


def test_validate_schema_detects_int_user_id():
    payload = {"user_id": 12345, "email": "test@example.com"}
    result = validate_schema(payload, EXPECTED_SCHEMA)
    assert result.valid is False
    fields = [e.field for e in result.errors]
    assert "user_id" in fields


def test_validate_schema_passes_when_correct():
    payload = {"user_id": "12345", "email": "test@example.com"}
    result = validate_schema(payload, EXPECTED_SCHEMA)
    assert result.valid is True
    assert result.errors == []


def test_validate_schema_detects_missing_field():
    payload = {"email": "test@example.com"}
    result = validate_schema(payload, EXPECTED_SCHEMA)
    assert result.valid is False
    fields = [e.field for e in result.errors]
    assert "user_id" in fields


def test_simulate_replay_low_confidence_for_int_user_id():
    message = {"event": "user_created", "schema_version": 2}
    fix = {"payload": {"user_id": 12345, "email": "test@example.com"}}
    result = simulate_replay(message, fix)
    assert result.success_likelihood == "low"
    assert result.confidence < 0.5


def test_simulate_replay_high_confidence_for_string_user_id():
    message = {"event": "user_created", "schema_version": 2}
    fix = {"payload": {"user_id": "12345", "email": "test@example.com"}}
    result = simulate_replay(message, fix)
    assert result.success_likelihood == "high"
    assert result.confidence > 0.8


def test_simulate_replay_low_confidence_for_missing_payload():
    message = {"event": "user_created", "schema_version": 2}
    fix = {}
    result = simulate_replay(message, fix)
    assert result.success_likelihood == "low"
    assert result.confidence < 0.2
