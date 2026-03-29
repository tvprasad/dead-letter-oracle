from pydantic import BaseModel


# dlq.read_message
class ReadMessageInput(BaseModel):
    file_path: str


class DLQMessage(BaseModel):
    event: str
    schema_version: int
    payload: dict
    error: str | None = None


# schema.validate
class FieldError(BaseModel):
    field: str
    expected_type: str
    actual_type: str


class ValidateInput(BaseModel):
    payload: dict
    expected_schema: dict


class ValidateOutput(BaseModel):
    valid: bool
    errors: list[FieldError]


# replay.simulate
class SimulateInput(BaseModel):
    original_message: dict
    proposed_fix: dict


class SimulateOutput(BaseModel):
    success_likelihood: str  # "low" | "medium" | "high"
    confidence: float
    reason: str


# agent.run_incident
class TraceEntry(BaseModel):
    step: int
    summary: str
    detail: str = ""


class GatekeeperOutput(BaseModel):
    decision: str  # ALLOW | WARN | BLOCK
    confidence: float
    reasons: list[str]


class RunIncidentOutput(BaseModel):
    message: dict
    validation: dict
    initial_fix: str
    simulation1: dict
    revised_fix: str
    simulation2: dict
    gatekeeper: GatekeeperOutput
    trace: list[TraceEntry]
