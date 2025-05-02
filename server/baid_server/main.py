import os
import dotenv
import logging
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from vertexai.preview import reasoning_engines
from google.adk.sessions import VertexAiSessionService
import sqlite3
from typing import Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("adk_server")

dotenv.load_dotenv()

app = FastAPI()

# Read agent_engine_id from environment variable, file, or fallback to default
AGENT_ENGINE_ID = 'projects/742371152853/locations/us-central1/reasoningEngines/988619283045023744'
if not AGENT_ENGINE_ID and os.path.exists("../agent_resource.txt"):
    with open("../agent_resource.txt") as f:
        AGENT_ENGINE_ID = f.read().strip()
if not AGENT_ENGINE_ID:
    AGENT_ENGINE_ID = os.getenv("DEFAULT_AGENT_ENGINE_ID", "5899794676692549632")

logger.info(f"Using Agent Engine ID: {AGENT_ENGINE_ID}")

# Set up project information
PROJECT_ID = os.getenv("PROJECT_ID", "742371152853")
LOCATION = os.getenv("LOCATION", "us-central1")

# The app_name used with the session service should be the Reasoning Engine ID or name
REASONING_ENGINE_APP_NAME = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"

logger.info(f"Using Reasoning Engine App Name: {REASONING_ENGINE_APP_NAME}")

# Initialize the session service
try:
    session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)
    logger.info("Successfully initialized VertexAiSessionService")
except Exception as e:
    logger.error(f"Failed to initialize VertexAiSessionService: {str(e)}")
    raise


# Initialize the database for storing user-session mappings
def init_db():
    logger.info("Initializing database")
    try:
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
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


# Call init_db at startup
init_db()


@app.get("/")
def read_root():
    logger.info("Health check endpoint called")
    return {"message": "Server is running", "agent_engine_id": AGENT_ENGINE_ID}


# Initialize the ReasoningEngine
def get_agent():
    logger.debug("Getting ReasoningEngine instance")
    try:
        agent = reasoning_engines.ReasoningEngine(AGENT_ENGINE_ID)
        logger.debug("Successfully obtained ReasoningEngine instance")
        return agent
    except Exception as e:
        logger.error(f"Failed to get ReasoningEngine instance: {str(e)}")
        raise


# Store user-session mapping in SQLite
def store_session_mapping(user_id, session_id):
    logger.info(f"Storing/updating session mapping: user_id={user_id}, session_id={session_id}")
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO user_sessions (user_id, session_id) VALUES (?, ?)",
            (user_id, session_id)
        )
        conn.commit()
        logger.info(f"New session mapping created: user_id={user_id}, session_id={session_id}")
    except sqlite3.IntegrityError:
        # Session already exists, update last_used_at
        cursor.execute(
            "UPDATE user_sessions SET last_used_at = CURRENT_TIMESTAMP WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )
        conn.commit()
        logger.info(f"Updated existing session mapping: user_id={user_id}, session_id={session_id}")
    except Exception as e:
        logger.error(f"Error storing session mapping: {str(e)}")
        raise
    finally:
        conn.close()


# Check if a session exists in our local database
def session_exists(user_id, session_id):
    logger.debug(f"Checking if session exists: user_id={user_id}, session_id={session_id}")
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM user_sessions WHERE user_id = ? AND session_id = ?",
        (user_id, session_id)
    )
    result = cursor.fetchone()
    conn.close()

    exists = result is not None
    logger.debug(f"Session exists check result: {exists}")
    return exists


# Check if a session exists in Vertex AI
def vertex_session_exists(user_id, session_id):
    logger.debug(f"Checking if session exists in Vertex AI: user_id={user_id}, session_id={session_id}")
    try:
        session = session_service.get_session(
            app_name=REASONING_ENGINE_APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        logger.debug(f"Session found in Vertex AI: user_id={user_id}, session_id={session_id}")
        return True
    except Exception as e:
        logger.debug(f"Session not found in Vertex AI or error: {str(e)}")
        return False


@app.post("/consult")
async def consult(
        request: Request,
        user_id: Optional[str] = Header(None),
        session_id: Optional[str] = Header(None)
):
    request_id = os.urandom(4).hex()
    logger.info(f"[{request_id}] Received /consult request: user_id={user_id}, session_id={session_id}")

    data = await request.json()
    user_input = data.get("prompt", "")
    file_content = data.get("file_content", "")

    # If user_id not in header, fallback to body
    if not user_id:
        user_id = data.get("user_id", "default_user")
        logger.info(f"[{request_id}] No user_id in header, using from body or default: {user_id}")

    # Get the agent
    try:
        agent = get_agent()
    except Exception as e:
        logger.error(f"[{request_id}] Failed to get agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")

    # Simplified session logic - use provided session_id directly if available
    if not session_id:
        # No session_id provided, so create a new one
        logger.info(f"[{request_id}] No session_id provided, creating new session for user {user_id}")
        try:
            vertex_session = agent.create_session(user_id=user_id)
            session_id = vertex_session["id"]
            user_id = vertex_session["user_id"]

            logger.info(f"[{request_id}] Created new session in Vertex AI: user_id={user_id}, session_id={session_id}")

            # Store the mapping in our local database
            store_session_mapping(user_id, session_id)
        except Exception as e:
            logger.error(f"[{request_id}] Failed to create new session: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create new session: {str(e)}")
    else:
        # Session_id was provided - try to use it directly
        logger.info(f"[{request_id}] Using provided session_id: {session_id}")

        # Store mapping if not already in DB
        if not session_exists(user_id, session_id):
            logger.info(
                f"[{request_id}] Adding session mapping to local DB: user_id={user_id}, session_id={session_id}")
            store_session_mapping(user_id, session_id)
        else:
            logger.info(f"[{request_id}] Session mapping already exists in local DB")
            # Update the last_used_at timestamp
            store_session_mapping(user_id, session_id)

    # Query the agent using the provided or new session_id
    logger.info(
        f"[{request_id}] Querying agent with: user_id={user_id}, session_id={session_id}, prompt={user_input[:50]}...")
    try:
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

        logger.info(f"[{request_id}] Got response from agent of length {len(response_text)} characters")
        logger.debug(f"[{request_id}] Response preview: {response_text[:100]}...")
    except Exception as e:
        logger.error(f"[{request_id}] Error querying agent with provided session: {str(e)}")

        # If using the provided session_id fails, only then try creating a new session
        logger.warning(f"[{request_id}] Failed to use provided session_id. Creating new session as fallback.")
        try:
            vertex_session = agent.create_session(user_id=user_id)
            old_session_id = session_id
            session_id = vertex_session["id"]
            user_id = vertex_session["user_id"]

            logger.info(
                f"[{request_id}] Created new session in Vertex AI: user_id={user_id}, session_id={session_id} (replacing {old_session_id})")

            # Store the mapping in our local database
            store_session_mapping(user_id, session_id)

            # Try again with the new session
            response_text = ""
            for event in agent.stream_query(
                    user_id=user_id,
                    session_id=session_id,
                    message=user_input
            ):
                for part in event.get("content", {}).get("parts", []):
                    if "text" in part:
                        response_text += part["text"]

            logger.info(f"[{request_id}] Got response with new session of length {len(response_text)} characters")
        except Exception as e2:
            logger.error(f"[{request_id}] Failed with fallback session as well: {str(e2)}")
            raise HTTPException(status_code=500,
                                detail=f"Failed to query agent with both provided and new session: {str(e)} | {str(e2)}")

    logger.info(f"[{request_id}] Successfully completed /consult request")

    return JSONResponse(
        content={
            "response": response_text,
            "session_id": session_id,
            "user_id": user_id
        }
    )


@app.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    request_id = os.urandom(4).hex()
    logger.info(f"[{request_id}] Received /sessions request for user_id={user_id}")

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

    logger.info(f"[{request_id}] Found {len(sessions)} sessions in local DB for user_id={user_id}")

    if not sessions:
        # If not found in local DB, try to get from ADK (this is a fallback)
        logger.info(f"[{request_id}] No sessions found in local DB, trying ADK for user_id={user_id}")
        try:
            adk_sessions = session_service.list_sessions(
                app_name=REASONING_ENGINE_APP_NAME,
                user_id=user_id
            )

            logger.info(f"[{request_id}] Found {len(adk_sessions)} sessions in ADK for user_id={user_id}")

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
            logger.warning(f"[{request_id}] Error getting sessions from ADK: {str(e)}")
            # If still no sessions found, return 404
            if not sessions:
                logger.error(f"[{request_id}] No sessions found for user {user_id} in both local DB and ADK")
                raise HTTPException(status_code=404, detail=f"No sessions found for user {user_id}")

    logger.info(f"[{request_id}] Successfully completed /sessions request for user_id={user_id}")

    return {"user_id": user_id, "sessions": sessions}


@app.get("/history/{user_id}/{session_id}")
async def get_session_history(user_id: str, session_id: str):
    request_id = os.urandom(4).hex()
    logger.info(f"[{request_id}] Received /history request for user_id={user_id}, session_id={session_id}")

    # First check if the session exists in our local DB
    if not session_exists(user_id, session_id):
        logger.warning(f"[{request_id}] Session {session_id} not found for user {user_id} in local DB")
        # This is fine - just log it but continue

    try:
        # The error suggests there's an issue with the app_name format
        # Let's try using just the AGENT_ENGINE_ID directly without adding project/location prefixes
        logger.info(f"[{request_id}] Retrieving session history: user_id={user_id}, session_id={session_id}")

        # Direct approach using the ReasoningEngine API
        agent = get_agent()

        # Get the messages directly from the agent using the stream_history method or similar
        history = []
        try:
            # Query the history using the Vertex AI Reasoning Engine client directly
            # This bypasses the ADK session service which seems to have formatting issues

            # Note: We don't use session_service.get_session here because of the app_name issue
            # Instead, we'll use a direct approach to get the conversation history

            # Using ReasoningEngine API directly (if available)
            # Check if the agent has a method like get_history or list_messages
            if hasattr(agent, 'get_history'):
                messages = agent.get_history(user_id=user_id, session_id=session_id)
                for msg in messages:
                    if msg.get('role') == 'user':
                        history.append({
                            "role": "user",
                            "message": msg.get('content', ''),
                            "timestamp": msg.get('timestamp', None)
                        })
                    else:
                        history.append({
                            "role": "agent",
                            "message": msg.get('content', ''),
                            "timestamp": msg.get('timestamp', None)
                        })
            else:
                # If there's no direct method, we'll need to use a workaround
                # One approach is to store history in our local database during each consult call
                # Since we haven't implemented that yet, let's extract this information
                # from our local database for now

                conn = sqlite3.connect('sessions.db')
                cursor = conn.cursor()

                # Add a query to get messages if you have them stored locally
                # For now, return a placeholder message
                history.append({
                    "role": "system",
                    "message": "History retrieval is currently limited. We're tracking session existence but not message content in the local database.",
                    "timestamp": datetime.now().timestamp()
                })

                conn.close()

                logger.warning(
                    f"[{request_id}] Limited history retrieval capability. Consider implementing local message storage.")
        except Exception as e:
            logger.error(f"[{request_id}] Error retrieving conversation history: {str(e)}")
            # Fall back to a simpler approach - inform user that detailed history isn't available
            history.append({
                "role": "system",
                "message": "We're unable to retrieve the detailed conversation history at this time.",
                "timestamp": datetime.now().timestamp()
            })

        logger.info(f"[{request_id}] Retrieved {len(history)} messages for session {session_id}")

        return {
            "user_id": user_id,
            "session_id": session_id,
            "history": history,
            "note": "Session exists, but detailed history retrieval may be limited."
        }

    except Exception as e:
        logger.error(f"[{request_id}] Error in history endpoint: {str(e)}")

        # Return a more informative error response
        return JSONResponse(
            status_code=500,
            content={
                "user_id": user_id,
                "session_id": session_id,
                "error": str(e),
                "note": "There was an error retrieving the full history. The Vertex AI API may have changed or the session format is different than expected.",
                "workaround": "You can continue using this session for conversations, even though we can't retrieve its history."
            }
        )

@app.delete("/sessions/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    request_id = os.urandom(4).hex()
    logger.info(f"[{request_id}] Received /delete request for user_id={user_id}, session_id={session_id}")

    # First check if the session exists in our local DB
    if not session_exists(user_id, session_id):
        logger.warning(f"[{request_id}] Session {session_id} not found for user {user_id} in local DB")

        # Check if it exists in Vertex AI
        try:
            vertex_exists = vertex_session_exists(user_id, session_id)
            if vertex_exists:
                logger.info(f"[{request_id}] Session found in Vertex AI but not in local DB.")
            else:
                logger.error(
                    f"[{request_id}] Session {session_id} not found for user {user_id} in both local DB and Vertex AI")
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found for user {user_id}")
        except Exception as e:
            logger.error(f"[{request_id}] Error checking session in Vertex AI: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or error checking: {str(e)}")

    try:
        # Delete from ADK
        logger.info(f"[{request_id}] Deleting session from ADK: user_id={user_id}, session_id={session_id}")
        session_service.delete_session(
            app_name=REASONING_ENGINE_APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        logger.info(f"[{request_id}] Successfully deleted session from ADK")

        # Delete from our local DB
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM user_sessions WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"[{request_id}] Deleted {deleted_count} row(s) from local DB")

        return {"message": f"Session {session_id} for user {user_id} deleted successfully"}

    except Exception as e:
        logger.error(f"[{request_id}] Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("baid_server.main:app", host="0.0.0.0", port=port)
