import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from .planner import run_incident

app = FastAPI(title="Dead Letter Oracle — Agent API", version="1.0.0")


class IncidentRequest(BaseModel):
    file_path: str = "data/sample_dlq.json"


@app.post("/run-incident")
def run_incident_endpoint(request: IncidentRequest):
    """
    Run the full governed incident loop:
      read -> validate -> propose -> simulate -> revise -> simulate -> govern -> trace
    Returns a structured result with gatekeeper decision and BlackBox trace.
    """
    return run_incident(request.file_path)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("agent.api:app", host="0.0.0.0", port=8000, reload=False)  # nosec B104
