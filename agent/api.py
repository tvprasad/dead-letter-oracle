import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from mcp_server.tools import run_incident

app = FastAPI(title="Dead Letter Oracle — Agent API", version="1.0.0")


class IncidentRequest(BaseModel):
    file_path: str = "data/sample_dlq.json"


@app.post("/run-incident")
def run_incident_endpoint(request: IncidentRequest):
    """
    Run the full governed incident loop via HTTP.
    Delegates to agent_run_incident MCP tool (mcp_server/tools.py).
    """
    return run_incident(request.file_path)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("agent.api:app", host="0.0.0.0", port=8000, reload=False)  # nosec B104
