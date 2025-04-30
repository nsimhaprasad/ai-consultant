import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Read agent_host from environment variable, file, or fallback to default
AGENT_HOST = os.getenv("AGENT_HOST")
if not AGENT_HOST and os.path.exists("agent_resource.txt"):
    with open("agent_resource.txt") as f:
        AGENT_HOST = f.read().strip()
if not AGENT_HOST:
    AGENT_HOST = os.getenv("DEFAULT_AGENT_HOST", "projects/742371152853/locations/us-central1/reasoningEngines/5899794676692549632")

@app.get("/")
def read_root():
    return {"message": "Server is running", "agent_host": AGENT_HOST}

# Placeholder endpoint for plugin to call
@app.post("/consult")
async def consult(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    file_content = data.get("file_content", "")
    # Basic echo logic for demonstration
    return JSONResponse(content={
        "status": "ok",
        "received_prompt": prompt,
        "received_file_content_preview": file_content[:200],  # preview first 200 chars
        "agent_host": AGENT_HOST
    })
