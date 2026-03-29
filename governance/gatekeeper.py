from dataclasses import dataclass, field

# Demo environment — flip to "prod" to see BLOCK behaviour
ENVIRONMENT = "prod"

CONFIDENCE_ALLOW = 0.80
CONFIDENCE_WARN = 0.50


@dataclass
class GatekeeperResult:
    decision: str  # ALLOW | WARN | BLOCK
    confidence: float
    reasons: list[str] = field(default_factory=list)


def evaluate(
    validation: dict,
    simulation: dict,
    fix_applied: bool,
) -> GatekeeperResult:
    """
    Multi-factor replay evaluation.

    Factors:
      1. Schema validation result
      2. Replay simulation confidence
      3. Whether the proposed fix resolved the root issue
      4. Deployment environment (prod vs dev)
    """
    reasons: list[str] = []
    confidence: float = simulation.get("confidence", 0.0)
    schema_valid: bool = validation.get("valid", False)

    # ── Factor 1: schema compatibility ───────────────────────
    if schema_valid:
        reasons.append("Schema validation passes — no field mismatches remaining")
    elif fix_applied:
        reasons.append(
            "Schema mismatch detected in original message — proposed fix addresses it but has not been applied live"
        )
    else:
        reasons.append("Schema mismatch detected — no confirmed fix applied")

    # ── Factor 2: replay simulation confidence ────────────────
    sim_reason = simulation.get("reason", "")
    if confidence >= CONFIDENCE_ALLOW:
        reasons.append(f"Replay simulation confidence is high ({confidence}) — {sim_reason}")
    elif confidence >= CONFIDENCE_WARN:
        reasons.append(f"Replay simulation confidence is marginal ({confidence}) — {sim_reason}")
    else:
        reasons.append(f"Replay simulation confidence is low ({confidence}) — {sim_reason}")

    # ── Factor 3: fix resolution ──────────────────────────────
    if fix_applied:
        reasons.append("Proposed fix resolves the field type mismatch")
    else:
        reasons.append("No confirmed fix applied to root cause")

    # ── Factor 4: environment ─────────────────────────────────
    reasons.append(f"Environment is {ENVIRONMENT}")

    # ── Decision logic ────────────────────────────────────────
    if not fix_applied or confidence < CONFIDENCE_WARN:
        decision = "BLOCK"
    elif confidence < CONFIDENCE_ALLOW or not schema_valid:
        decision = "WARN"
    elif ENVIRONMENT == "prod" and confidence < CONFIDENCE_ALLOW:
        decision = "WARN"
    else:
        decision = "ALLOW"

    return GatekeeperResult(decision=decision, confidence=confidence, reasons=reasons)
