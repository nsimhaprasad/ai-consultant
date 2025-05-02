import os
import dotenv
import logging
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from vertexai.preview import reasoning_engines
from google.adk.sessions import VertexAiSessionService
import sqlite3
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import jwt
import httpx
from threading import Timer

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

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"

# Set this to the exact redirect URI registered in Google Cloud Console
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8080/api/auth/google-login")


class GoogleCodeRequest(BaseModel):
    code: str
    redirect_uri: str


class GoogleTokenRequest(BaseModel):
    google_token: str


# Temporary in-memory session storage for OAuth states (for demo; use Redis/db in prod)
oauth_sessions: Dict[str, dict] = {}
OAUTH_SESSION_TTL = 300  # 5 minutes


def cleanup_state(state):
    oauth_sessions.pop(state, None)


@app.get("/api/auth/google-login")
async def google_login_redirect(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code or not state:
        html_content = """
        <html><body><h2>Login failed!</h2><p>Missing code or state.</p></body></html>
        """
        return HTMLResponse(content=html_content, status_code=400)
    redirect_uri = REDIRECT_URI
    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        if token_resp.status_code != 200:
            html_content = f"""
            <html><body><h2>Login failed!</h2><p>Failed to exchange code for token: {token_resp.text}</p></body></html>
            """
            return HTMLResponse(content=html_content, status_code=400)
        tokens = token_resp.json()
        access_token = tokens["access_token"]
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
        if resp.status_code != 200:
            html_content = f"""
            <html><body><h2>Login failed!</h2><p>Failed to get user info: {resp.text}</p></body></html>
            """
            return HTMLResponse(content=html_content, status_code=400)
        userinfo = resp.json()
        store_user(userinfo)
        backend_token = jwt.encode({
            "sub": userinfo["email"],
            "name": userinfo["name"],
            "picture": userinfo.get("picture"),
            "exp": (datetime.utcnow() + timedelta(hours=8)).timestamp()
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)
        # Store in-memory session for plugin to fetch
        oauth_sessions[state] = {
            "access_token": backend_token,
            "expires_in": 8 * 3600,
            "email": userinfo["email"],
            "name": userinfo["name"],
            "picture": userinfo.get("picture"),
            "error": None
        }
        Timer(OAUTH_SESSION_TTL, cleanup_state, args=[state]).start()
        html_content = """
        <html><head><title>Login Successful</title></head><body style='font-family:sans-serif;text-align:center;margin-top:10em;'><h2>Login successful!</h2><p>You may now return to your IDE to enjoy BAID agent.</p><p>You can close this window.</p></body></html>"""
        return HTMLResponse(content=html_content, status_code=200)
    except Exception as e:
        html_content = f"""
        <html><body><h2>Login failed!</h2><p>{str(e)}</p></body></html>
        """
        return HTMLResponse(content=html_content, status_code=500)


@app.get("/api/auth/session")
async def get_oauth_session(state: str):
    session = oauth_sessions.get(state)
    if not session:
        return JSONResponse(status_code=404, content={"error": "Session not found or expired"})
    return JSONResponse(content=session)


# --- User DB logic ---
def store_user(userinfo):
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            picture TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        cursor.execute('''INSERT OR IGNORE INTO users (email, name, picture) VALUES (?, ?, ?)''',
                       (userinfo["email"], userinfo["name"], userinfo.get("picture")))
        conn.commit()
    except Exception as e:
        logger.error(f"Error storing user: {str(e)}")
    finally:
        conn.close()


# Auth dependency for /consult
bearer_scheme = HTTPBearer()


def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


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

# Extract just the ID part from the full resource name
AGENT_ENGINE_ID_ONLY = AGENT_ENGINE_ID.split('/')[-1]
logger.info(f"Extracted Agent Engine ID: {AGENT_ENGINE_ID_ONLY}")

# The app_name used with the session service should be the Reasoning Engine ID or name
# Using just the numeric ID as indicated by _parse_reasoning_engine_id method in VertexAiSessionService
REASONING_ENGINE_APP_NAME = AGENT_ENGINE_ID_ONLY

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
        # Create messages table for storing chat history as backup
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        # Create users table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            name TEXT,
            picture TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
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


# Store message in SQLite (as backup)
def store_message(user_id, session_id, role, content):
    logger.debug(f"Storing message: user_id={user_id}, session_id={session_id}, role={role}")
    conn = sqlite3.connect('sessions.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (user_id, session_id, role, content) VALUES (?, ?, ?, ?)",
            (user_id, session_id, role, content)
        )
        conn.commit()
        logger.debug(f"Message stored successfully")
    except Exception as e:
        logger.error(f"Error storing message: {str(e)}")
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
        token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        # FastAPI expects the header name to exactly match, including case sensitivity
        session_id: Optional[str] = Header(None, alias="session_id")  # Explicitly set alias
):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = payload["sub"]
    request_id = os.urandom(4).hex()

    # Better logging to debug the issue
    logger.info(f"[{request_id}] Received /consult request: user_id={user_id}")
    logger.info(f"[{request_id}] session_id header value: {session_id}")
    logger.info(f"[{request_id}] session_id header type: {type(session_id)}")

    # Also try to get the header manually to debug
    manual_session_id = request.headers.get("session_id") or request.headers.get("Session-Id")
    logger.info(f"[{request_id}] Manual header lookup: {manual_session_id}")

    data = await request.json()
    user_input = data.get("prompt", "")
    file_content = data.get("file_content", "")

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

    # Store user message in local DB (backup)
    store_message(user_id, session_id, "user", user_input)

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

        # Store agent response in local DB (backup)
        store_message(user_id, session_id, "agent", response_text)
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

            # Store user message in new session
            store_message(user_id, session_id, "user", user_input)

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

            # Store agent response in local DB for new session
            store_message(user_id, session_id, "agent", response_text)

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

            logger.info(f"[{request_id}] Found {len(adk_sessions.sessions)} sessions in ADK for user_id={user_id}")

            for session in adk_sessions.sessions:
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
        # Store it if it exists in Vertex AI but not in local DB
        try:
            if vertex_session_exists(user_id, session_id):
                logger.info(f"[{request_id}] Session found in Vertex AI but not in local DB. Adding to local DB.")
                store_session_mapping(user_id, session_id)
            else:
                logger.error(f"[{request_id}] Session not found in both DB and Vertex AI")
                raise HTTPException(status_code=404, detail=f"Session {session_id} not found for user {user_id}")
        except Exception as e:
            logger.error(f"[{request_id}] Error checking Vertex AI session: {str(e)}")
            # Continue anyway, we'll try other methods

    try:
        # First try to get history from ADK's session service
        logger.info(f"[{request_id}] Trying to get history from ADK session service")
        session = session_service.get_session(
            app_name=REASONING_ENGINE_APP_NAME,
            user_id=user_id,
            session_id=session_id
        )

        # Check if we have events in the session
        if hasattr(session, 'events') and session.events:
            logger.info(f"[{request_id}] Found {len(session.events)} events in ADK session")

            # Extract the events (chat history)
            history = []

            for event in session.events:
                try:
                    # Process each event to extract message content
                    message_text = ""
                    if (hasattr(event, 'content') and
                            hasattr(event.content, 'parts') and
                            event.content.parts):

                        # Collect text from all parts
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                message_text += part.text

                    # If we found text content and have author info
                    if message_text and hasattr(event, 'author'):
                        # Determine role based on author field
                        role = "user" if event.author == "user" else "agent"

                        # Add to history
                        history.append({
                            "role": role,
                            "message": message_text,
                            "timestamp": event.timestamp if hasattr(event, 'timestamp') else None
                        })
                        logger.debug(f"[{request_id}] Added {role} message: {message_text[:50]}...")
                except Exception as e:
                    logger.warning(f"[{request_id}] Error processing event: {str(e)}")

            # Sort by timestamp
            history.sort(key=lambda x: x["timestamp"] if x["timestamp"] is not None else 0)

            logger.info(f"[{request_id}] Successfully formatted {len(history)} messages from ADK session")

            if history:
                return {
                    "user_id": user_id,
                    "session_id": session_id,
                    "history": history,
                    "source": "vertex_ai_session_service"
                }
            else:
                logger.warning(f"[{request_id}] No messages extracted from events, falling back to local DB")
        else:
            logger.warning(f"[{request_id}] No events found in ADK session, falling back to local DB")
    except Exception as e:
        logger.warning(f"[{request_id}] Error getting history from ADK session service: {str(e)}")
        # Continue to try local DB

    # Fall back to local database if ADK session service fails
    logger.info(f"[{request_id}] Trying to get history from local database")
    try:
        conn = sqlite3.connect('sessions.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE user_id = ? AND session_id = ? ORDER BY timestamp ASC",
            (user_id, session_id)
        )

        history = []
        for row in cursor.fetchall():
            history.append({
                "role": row[0],
                "message": row[1],
                "timestamp": row[2]
            })

        conn.close()

        if history:
            logger.info(f"[{request_id}] Found {len(history)} messages in local DB")
            return {
                "user_id": user_id,
                "session_id": session_id,
                "history": history,
                "source": "local_database"
            }
        else:
            logger.warning(f"[{request_id}] No messages found in local DB")
            # Return a placeholder message
            return {
                "user_id": user_id,
                "session_id": session_id,
                "history": [{
                    "role": "system",
                    "message": "Session exists, but no message history was found. You can continue the conversation.",
                    "timestamp": datetime.now().timestamp()
                }],
                "note": "Session exists, but no message history was found."
            }
    except Exception as e:
        logger.error(f"[{request_id}] Error getting history from local DB: {str(e)}")

        # All retrieval methods failed, return an informative error
        return JSONResponse(
            content={
                "user_id": user_id,
                "session_id": session_id,
                "history": [{
                    "role": "system",
                    "message": "We encountered an error retrieving the conversation history. You can continue using this session.",
                    "timestamp": datetime.now().timestamp()
                }],
                "error": str(e),
                "note": "Error retrieving history, but the session is still valid for continued conversation."
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

        # Delete session mapping
        cursor.execute(
            "DELETE FROM user_sessions WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )
        deleted_count = cursor.rowcount

        # Delete associated messages
        cursor.execute(
            "DELETE FROM messages WHERE user_id = ? AND session_id = ?",
            (user_id, session_id)
        )
        deleted_messages = cursor.rowcount

        conn.commit()
        conn.close()

        logger.info(
            f"[{request_id}] Deleted {deleted_count} session(s) and {deleted_messages} message(s) from local DB")

        return {"message": f"Session {session_id} for user {user_id} deleted successfully"}

    except Exception as e:
        logger.error(f"[{request_id}] Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)
