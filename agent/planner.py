import json

from governance.gatekeeper import evaluate as gatekeeper_evaluate
from observability.blackbox import trace

from . import llm
from .runtime import run_tool_calls

EXPECTED_SCHEMA = {
    "user_id": "string",
    "email": "string",
}

DLQ_FILE = "data/sample_dlq.json"

WEAK_FIX_PAYLOAD = {
    "user_id": 12345,  # still an int — simulation will flag this
    "email": "test@example.com",
}
STRONG_FIX_PAYLOAD = {
    "user_id": "12345",  # coerced to string — simulation passes
    "email": "test@example.com",
}

SEP = "=" * 56


def run():
    print("\n[ Dead Letter Oracle ] Starting...\n")

    # ── Step 1: read DLQ message ──────────────────────────────
    results = run_tool_calls([("dlq_read_message", {"file_path": DLQ_FILE})])
    message = json.loads(results[0]["result"])
    trace.record(
        "Read message from DLQ",
        f"event={message['event']} schema_version={message['schema_version']}",
    )

    # ── Step 2: validate schema ───────────────────────────────
    results = run_tool_calls(
        [
            (
                "schema_validate",
                {
                    "payload": message["payload"],
                    "expected_schema": EXPECTED_SCHEMA,
                },
            )
        ]
    )
    validation = json.loads(results[0]["result"])

    field_errors = validation.get("errors", [])
    if field_errors:
        e = field_errors[0]
        trace.record(
            "Detected schema mismatch",
            f"'{e['field']}' expected {e['expected_type']}, got {e['actual_type']}",
        )
    else:
        trace.record("Schema validation passed")

    # ── Step 3: print diagnosis ───────────────────────────────
    print(SEP)
    print("Diagnosis:")
    print(f"  Event:      {message['event']}")
    print(f"  Schema ver: {message['schema_version']}")
    print(f"  DLQ error:  {message.get('error', 'none')}")
    print(f"  Validation: {'passed' if validation['valid'] else 'FAILED'}")
    for e in field_errors:
        print(f"  Field:      '{e['field']}' expected {e['expected_type']}, got {e['actual_type']}")
    print(SEP)

    # ── Step 4: LLM proposes initial fix ──────────────────────
    print("\n[ Agent ] Asking LLM for initial fix proposal...")
    initial_fix = llm.propose_initial_fix(message, validation)
    print(f"\n[ LLM  ] Initial fix proposal:\n  {initial_fix}\n")
    trace.record("Proposed initial fix", _truncate(initial_fix, 80))

    # ── Step 5: replay.simulate — weak fix ───────────────────
    print("[ Agent ] Simulating replay with proposed fix...")
    results = run_tool_calls(
        [
            (
                "replay_simulate",
                {
                    "original_message": message,
                    "proposed_fix": {"payload": WEAK_FIX_PAYLOAD},
                },
            )
        ]
    )
    simulation = json.loads(results[0]["result"])
    trace.record(
        f"Simulation result: {simulation['success_likelihood']} confidence ({simulation['confidence']})",
        simulation["reason"],
    )

    print(SEP)
    print("Simulation result:")
    print(f"  Likelihood: {simulation['success_likelihood']}")
    print(f"  Confidence: {simulation['confidence']}")
    print(f"  Reason:     {simulation['reason']}")
    print(SEP)

    # ── Step 6: LLM revises ───────────────────────────────────
    print("\n[ Agent ] Simulation confidence low -- asking LLM to revise...\n")
    revised_fix = llm.revise_recommendation(initial_fix, simulation)
    print(f"[ LLM  ] Revised recommendation:\n  {revised_fix}\n")
    trace.record("Revised fix after low-confidence simulation", _truncate(revised_fix, 80))

    # ── Step 7: replay.simulate — strong fix ─────────────────
    print("[ Agent ] Re-simulating with corrected fix...")
    results = run_tool_calls(
        [
            (
                "replay_simulate",
                {
                    "original_message": message,
                    "proposed_fix": {"payload": STRONG_FIX_PAYLOAD},
                },
            )
        ]
    )
    simulation2 = json.loads(results[0]["result"])
    trace.record(
        f"Re-simulation result: {simulation2['success_likelihood']} confidence ({simulation2['confidence']})",
        simulation2["reason"],
    )

    print(SEP)
    print("Final simulation result:")
    print(f"  Likelihood: {simulation2['success_likelihood']}")
    print(f"  Confidence: {simulation2['confidence']}")
    print(f"  Reason:     {simulation2['reason']}")
    print(SEP)
    print("\n[ Agent ] Reasoning loop complete.\n")

    # ── Step 8: Gatekeeper ────────────────────────────────────
    print("[ Gatekeeper ] Evaluating replay safety...\n")
    gate = gatekeeper_evaluate(
        validation=validation,
        simulation=simulation2,
        fix_applied=(simulation2["confidence"] >= 0.80),
    )
    trace.record(
        f"Gatekeeper decision: {gate.decision}",
        f"confidence={gate.confidence} | {gate.reasons[0]}",
    )

    icons = {"ALLOW": "[OK]  ", "WARN": "[WARN]", "BLOCK": "[STOP]"}
    icon = icons.get(gate.decision, "      ")

    print(SEP)
    print(f"Gatekeeper Decision: {icon} {gate.decision}")
    print(f"Confidence:          {gate.confidence}")
    print("Reasons:")
    for r in gate.reasons:
        print(f"  - {r}")
    print(SEP)

    # ── BlackBox trace ────────────────────────────────────────
    print()
    trace.render()
    print()


def _truncate(text: str, max_len: int) -> str:
    text = text.replace("\n", " ")
    return text[:max_len] + "..." if len(text) > max_len else text
