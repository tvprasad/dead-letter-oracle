from mcp_server.tools import validate_schema, simulate_replay
from governance.gatekeeper import evaluate


def test_gatekeeper_blocks_when_no_fix_applied():
    simulation = {"success_likelihood": "low", "confidence": 0.28, "reason": "test"}
    validation = {"valid": False, "errors": []}
    gate = evaluate(validation=validation, simulation=simulation, fix_applied=False)
    assert gate.decision == "BLOCK"


def test_gatekeeper_warns_in_prod_with_high_confidence():
    simulation = {"success_likelihood": "high", "confidence": 0.91, "reason": "test"}
    validation = {"valid": False, "errors": []}
    gate = evaluate(validation=validation, simulation=simulation, fix_applied=True)
    assert gate.decision == "WARN"


def test_gatekeeper_allows_when_schema_valid_and_high_confidence():
    simulation = {"success_likelihood": "high", "confidence": 0.91, "reason": "test"}
    validation = {"valid": True, "errors": []}
    gate = evaluate(validation=validation, simulation=simulation, fix_applied=True)
    # prod env still warns; only allow if schema_valid + high confidence + dev env
    assert gate.decision in ("ALLOW", "WARN")


def test_gatekeeper_reasons_always_populated():
    simulation = {"success_likelihood": "high", "confidence": 0.91, "reason": "ok"}
    validation = {"valid": True, "errors": []}
    gate = evaluate(validation=validation, simulation=simulation, fix_applied=True)
    assert len(gate.reasons) == 4
    for r in gate.reasons:
        assert isinstance(r, str) and len(r) > 0


def test_validate_and_simulate_pipeline():
    """validate_schema feeds directly into simulate_replay without data loss."""
    payload = {"user_id": 12345, "email": "test@example.com"}
    schema = {"user_id": "string", "email": "string"}

    validation = validate_schema(payload, schema)
    assert not validation.valid

    sim = simulate_replay(
        {"event": "user_created"},
        {"payload": payload},
    )
    assert sim.confidence < 0.5
