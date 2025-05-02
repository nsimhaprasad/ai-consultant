import os
import dotenv
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from vertexai.preview import reasoning_engines
from google.adk.sessions import VertexAiSessionService
import sqlite3
from typing import Optional
from datetime import datetime

dotenv.load_dotenv()

app = FastAPI()

# Read agent_engine_id from environment variable, file, or fallback to default
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")
if not AGENT_ENGINE_ID and os.path.exists("../agent_resource.txt"):
    with open("../agent_resource.txt") as f:
        AGENT_ENGINE_ID = f.read().strip()
if not AGENT_ENGINE_ID:
    AGENT_ENGINE_ID = os.getenv("DEFAULT_AGENT_ENGINE_ID", "5899794676692549632")

# Set up project information
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")

# The app_name used with the session service should be the Reasoning Engine ID or name
REASONING_ENGINE_APP_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"

# Initialize the session service
session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)


# Initialize the database for storing user-session mappings
def init_db():
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        session_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, session_id)
    )
    ''')
    conn.commit()
    conn.close()


# Call init_db at startup
init_db()


@app.get("/")
def read_root():
    return {"message": "Server is running", "agent_engine_id": AGENT_ENGINE_ID}


# Initialize the ReasoningEngine
def get_agent():
    return reasoning_engines.ReasoningEngine(AGENT_ENGINE_ID)


# Store user-session mapping in SQLite
def store_session_mapping(user_id, session_id):
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO user_sessions (user_id, session_id) VALUES (?, ?)",
            (user_id, session_id)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Session already exists, update last_used_at
        cursor.execute(
            "UPDATE user_sessions SET last_used_at = CURRENT_TIMESTAMP WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )
        conn.commit()
    finally:
        conn.close()


# Check if a session exists in our local database
def session_exists(user_id, session_id):
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM user_sessions WHERE user_id = ? AND session_id = ?",
        (user_id, session_id)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


@app.post("/consult")
async def consult(
        request: Request,
        user_id: Optional[str] = Header(None),
        session_id: Optional[str] = Header(None)
):
    data = await request.json()
    user_input = data.get("prompt", "")
    file_content = data.get("file_content", "")

    # If user_id not in header, fallback to body
    if not user_id:
        user_id = data.get("user_id", "default_user")

    # Get the agent
    agent = get_agent()

    # Create a new session or use existing one
    if not session_id or not session_exists(user_id, session_id):
        # Create a new session in Vertex AI
        vertex_session = agent.create_session(user_id=user_id)
        session_id = vertex_session["id"]
        user_id = vertex_session["user_id"]

        # Store the mapping in our local database
        store_session_mapping(user_id, session_id)
    else:
        # Update the last_used_at timestamp
        store_session_mapping(user_id, session_id)

    # Query the agent using the session
    # The events are automatically recorded by Vertex AI
    response_text = ""
    for event in agent.stream_query(
            user_id=user_id,
            session_id=session_id,
            message=user_input
    ):
        for part in event.get("content", {}).get("parts", []):
            if "text" in part:
                response_text += part["text"]

    return JSONResponse(
        content={
            "response": response_text,
            "session_id": session_id,
            "user_id": user_id
        }
    )


@app.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    # Query our local database to find all sessions for this user
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT session_id, created_at, last_used_at FROM user_sessions WHERE user_id = ? ORDER BY last_used_at DESC",
        (user_id,)
    )

    sessions = []
    for row in cursor.fetchall():
        sessions.append({
            "session_id": row[0],
            "user_id": user_id,
            "created_at": row[1],
            "last_used_at": row[2]
        })

    conn.close()

    if not sessions:
        # If not found in local DB, try to get from ADK (this is a fallback)
        try:
            adk_sessions = session_service.list_sessions(
                app_name=REASONING_ENGINE_APP_NAME,
                user_id=user_id
            )

            for session in adk_sessions:
                # Store in our local DB for future reference
                store_session_mapping(user_id, session.id)

                sessions.append({
                    "session_id": session.id,
                    "user_id": user_id,
                    "created_at": datetime.fromtimestamp(session.last_update_time).isoformat(),
                    "last_used_at": datetime.fromtimestamp(session.last_update_time).isoformat()
                })
        except Exception as e:
            # If still no sessions found, return 404
            if not sessions:
                raise HTTPException(status_code=404, detail=f"No sessions found for user {user_id}")

    return {"user_id": user_id, "sessions": sessions}


@app.get("/history/{user_id}/{session_id}")
async def get_session_history(user_id: str, session_id: str):
    # First check if the session exists in our local DB
    if not session_exists(user_id, session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found for user {user_id}")

    try:
        # Get the session from ADK
        session = session_service.get_session(
            app_name=REASONING_ENGINE_APP_NAME,
            user_id=user_id,
            session_id=session_id
        )

        # Extract the events (message history)
        history = []
        for event in session.events:
            # The event types depend on how Vertex AI Reasoning Engine stores them
            # You may need to adjust these based on the actual event format
            if hasattr(event, "type"):
                if event.type in ["user_message", "user_request"]:
                    history.append({
                        "role": "user",
                        "message": event.payload.get("text", ""),
                        "timestamp": event.timestamp
                    })
                elif event.type in ["agent_response", "model_response"]:
                    history.append({
                        "role": "agent",
                        "message": event.payload.get("text", ""),
                        "timestamp": event.timestamp
                    })

        # Sort by timestamp
        history.sort(key=lambda x: x["timestamp"])

        return {
            "user_id": user_id,
            "session_id": session_id,
            "history": history
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error retrieving session history: {str(e)}")


@app.delete("/sessions/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    # First check if the session exists in our local DB
    if not session_exists(user_id, session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found for user {user_id}")

    try:
        # Delete from ADK
        session_service.delete_session(
            app_name=REASONING_ENGINE_APP_NAME,
            user_id=user_id,
            session_id=session_id
        )

        # Delete from our local DB
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM user_sessions WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )
        conn.commit()
        conn.close()

        return {"message": f"Session {session_id} for user {user_id} deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run("baid_server.main:app", host="0.0.0.0", port=port)