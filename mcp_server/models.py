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
