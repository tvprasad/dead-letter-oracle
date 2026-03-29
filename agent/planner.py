from mcp_server.tools import run_incident

SEP = "=" * 56


def run():
    """CLI entry point. Runs the governed incident loop and prints results."""
    print("\n[ Dead Letter Oracle ] Starting...\n")

    result = run_incident()

    message = result["message"]
    validation = result["validation"]
    field_errors = validation.get("errors", [])
    simulation1 = result["simulation1"]
    simulation2 = result["simulation2"]
    gate = result["gatekeeper"]

    # Diagnosis
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
