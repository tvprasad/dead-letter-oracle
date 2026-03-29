import json

from governance.gatekeeper import evaluate as gatekeeper_evaluate
from observability.blackbox import BlackBox

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


def run_incident(file_path: str = DLQ_FILE) -> dict:
    """
    Execute the full governed incident loop and return a structured result.

    Returns a dict with: message, validation, simulations, gatekeeper, trace.
    Caller decides how to surface the output (HTTP response, CLI print, test assertion).
    """
    trace = BlackBox()

    # ── Step 1: read DLQ message ──────────────────────────────
    results = run_tool_calls([("dlq_read_message", {"file_path": file_path})])
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

    # ── Step 3: LLM proposes initial fix ─────────────────────
    initial_fix = llm.propose_initial_fix(message, validation)
    trace.record("Proposed initial fix", _truncate(initial_fix, 80))

    # ── Step 4: replay.simulate — weak fix ───────────────────
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
    simulation1 = json.loads(results[0]["result"])
    trace.record(
        f"Simulation result: {simulation1['success_likelihood']} confidence ({simulation1['confidence']})",
        simulation1["reason"],
    )

    # ── Step 5: LLM revises ───────────────────────────────────
    revised_fix = llm.revise_recommendation(initial_fix, simulation1)
    trace.record("Revised fix after low-confidence simulation", _truncate(revised_fix, 80))

    # ── Step 6: replay.simulate — strong fix ─────────────────
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

    # ── Step 7: Gatekeeper ────────────────────────────────────
    gate = gatekeeper_evaluate(
        validation=validation,
        simulation=simulation2,
        fix_applied=(simulation2["confidence"] >= 0.80),
    )
    trace.record(
        f"Gatekeeper decision: {gate.decision}",
        f"confidence={gate.confidence} | {gate.reasons[0]}",
    )

    return {
        "message": message,
        "validation": validation,
        "initial_fix": initial_fix,
        "simulation1": simulation1,
        "revised_fix": revised_fix,
        "simulation2": simulation2,
        "gatekeeper": {
            "decision": gate.decision,
            "confidence": gate.confidence,
            "reasons": gate.reasons,
        },
        "trace": trace.entries(),
    }


def run():
    """CLI entry point. Runs the incident loop and prints results."""
    print("\n[ Dead Letter Oracle ] Starting...\n")

    result = run_incident()

    message = result["message"]
    validation = result["validation"]
    field_errors = validation.get("errors", [])
    simulation1 = result["simulation1"]
    simulation2 = result["simulation2"]
    gate = result["gatekeeper"]

    # ── Diagnosis ─────────────────────────────────────────────
    print(SEP)
    print("Diagnosis:")
    print(f"  Event:      {message['event']}")
    print(f"  Schema ver: {message['schema_version']}")
    print(f"  DLQ error:  {message.get('error', 'none')}")
    print(f"  Validation: {'passed' if validation['valid'] else 'FAILED'}")
    for e in field_errors:
        print(f"  Field:      '{e['field']}' expected {e['expected_type']}, got {e['actual_type']}")
    print(SEP)

    print(f"\n[ LLM  ] Initial fix proposal:\n  {result['initial_fix']}\n")

    print(SEP)
    print("Simulation result (initial fix):")
    print(f"  Likelihood: {simulation1['success_likelihood']}")
    print(f"  Confidence: {simulation1['confidence']}")
    print(f"  Reason:     {simulation1['reason']}")
    print(SEP)

    print(f"\n[ LLM  ] Revised recommendation:\n  {result['revised_fix']}\n")

    print(SEP)
    print("Final simulation result:")
    print(f"  Likelihood: {simulation2['success_likelihood']}")
    print(f"  Confidence: {simulation2['confidence']}")
    print(f"  Reason:     {simulation2['reason']}")
    print(SEP)
    print("\n[ Agent ] Reasoning loop complete.\n")

    icons = {"ALLOW": "[OK]  ", "WARN": "[WARN]", "BLOCK": "[STOP]"}
    icon = icons.get(gate["decision"], "      ")

    print(SEP)
    print(f"Gatekeeper Decision: {icon} {gate['decision']}")
    print(f"Confidence:          {gate['confidence']}")
    print("Reasons:")
    for r in gate["reasons"]:
        print(f"  - {r}")
    print(SEP)

    # ── BlackBox trace ────────────────────────────────────────
    print()
    _print_trace(result["trace"])
    print()


def _print_trace(entries: list[dict]) -> None:
    width = 56
    print("=" * width)
    print("BlackBox Trace")
    print("-" * width)
    for e in entries:
        print(f"{e['step']:>2}. {e['summary']}")
        if e.get("detail"):
            words = e["detail"].split()
            current = "      "
            for word in words:
                if len(current) + len(word) + 1 > 56:
                    print(current.rstrip())
                    current = "      " + word + " "
                else:
                    current += word + " "
            if current.strip():
                print(current.rstrip())
    print("=" * width)


def _truncate(text: str, max_len: int) -> str:
    text = text.replace("\n", " ")
    return text[:max_len] + "..." if len(text) > max_len else text
