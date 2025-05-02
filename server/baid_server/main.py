import os
import dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from vertexai.preview import reasoning_engines  # Updated import

dotenv.load_dotenv()

app = FastAPI()

# Read agent_engine_id from environment variable, file, or fallback to default
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
if not AGENT_ENGINE_ID and os.path.exists("../agent_resource.txt"):
    with open("../agent_resource.txt") as f:
        AGENT_ENGINE_ID = f.read().strip()
if not AGENT_ENGINE_ID:
    AGENT_ENGINE_ID = os.getenv("DEFAULT_AGENT_ENGINE_ID", "5899794676692549632")


@app.get("/")
def read_root():
    return {"message": "Server is running", "agent_engine_id": AGENT_ENGINE_ID}


# Updated endpoint for plugin to call
@app.post("/consult")
async def consult(request: Request):
    data = await request.json()
    user_input = data.get("prompt", "")
    file_content = data.get("file_content", "")
    user_id = data.get("user_id", "default_user")

    # Get the agent using the updated API
    agent = reasoning_engines.ReasoningEngine(AGENT_ENGINE_ID)

    # Create a session and query the agent
    session = agent.create_session(user_id=user_id)
    response_text = ""

    for event in agent.stream_query(
            user_id=session["user_id"],
            session_id=session["id"],
            message=user_input
    ):
        for part in event.get("content", {}).get("parts", []):
            if "text" in part:
                response_text += part["text"]

    return JSONResponse(content={"response": response_text})