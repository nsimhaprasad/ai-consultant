import os
import dotenv
import logging
import time
import asyncio
from typing import Optional, Dict
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from google.adk.sessions import VertexAiSessionService
from vertexai.preview import reasoning_engines
import asyncpg
from datetime import datetime, timedelta
from pydantic import BaseModel
import httpx
from threading import Timer
from google.cloud import secretmanager

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Only log to stdout
    ]
)
logger = logging.getLogger("adk_server")

dotenv.load_dotenv()

app = FastAPI()

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8080/api/auth/google-login")

# DB configuration - from secret manager by default
DB_CONNECTION_SECRET = os.environ.get("DB_CONNECTION_SECRET", "postgres-connection")

# Direct DB config for local dev and testing
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "ai_consultant_db")
DB_USER = os.environ.get("DB_USER", "baid-dev")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# Add streaming configuration
ENABLE_WORD_BY_WORD_STREAMING = os.getenv("ENABLE_WORD_BY_WORD_STREAMING", "true").lower() == "true"
logger.info(f"Word-by-word streaming: {'ENABLED' if ENABLE_WORD_BY_WORD_STREAMING else 'DISABLED'}")

# Project ID for Google Cloud
PROJECT_ID = os.getenv("PROJECT_ID", "742371152853")

# Database connection pool
db_pool = None


async def get_db_pool():
    """Get a connection pool to the PostgreSQL database."""
    global db_pool
    if db_pool is None:
        try:
            # Get connection string from Secret Manager in production or env vars in development
            if os.getenv("ENVIRONMENT") == "development" and DB_PASSWORD:
                # For local development, use env vars
                connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
                logger.info("Using local database connection from environment variables")
            else:
                # For production, get from Secret Manager
                connection_string = await get_secret(DB_CONNECTION_SECRET)
                logger.info(f"Using database connection from Secret Manager: {DB_CONNECTION_SECRET}")

            # Create connection pool
            db_pool = await asyncpg.create_pool(
                dsn=connection_string,
                min_size=1,
                max_size=10,
                timeout=30
            )

            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database connection pool: {str(e)}")
            raise
    return db_pool


async def get_secret(secret_id):
    """Get secret from Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {str(e)}")
        # Fallback for testing if explicitly set
        if os.getenv("ENVIRONMENT") == "testing":
            return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        raise


class GoogleCodeRequest(BaseModel):
    code: str
    redirect_uri: str


class GoogleTokenRequest(BaseModel):
    google_token: str


# In-memory session storage
oauth_sessions: Dict[str, dict] = {}
OAUTH_SESSION_TTL = 300


def cleanup_state(state):
    oauth_sessions.pop(state, None)


# Database functions - now using PostgreSQL with asyncpg
async def store_user(userinfo):
    """Store user in the database."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute('''
            INSERT INTO users (email, name, picture) 
            VALUES ($1, $2, $3)
            ON CONFLICT (email) 
            DO UPDATE SET name = $2, picture = $3
            ''', userinfo["email"], userinfo["name"], userinfo.get("picture"))
            logger.info(f"User stored/updated: {userinfo['email']}")
        except Exception as e:
            logger.error(f"Error storing user: {str(e)}")
            raise


async def store_session_mapping(user_id, session_id):
    """Store or update user session mapping."""
    logger.info(f"Storing/updating session mapping: user_id={user_id}, session_id={session_id}")
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute('''
            INSERT INTO user_sessions (user_id, session_id)
            VALUES ($1, $2)
            ON CONFLICT (user_id, session_id)
            DO UPDATE SET last_used_at = CURRENT_TIMESTAMP
            ''', user_id, session_id)
            logger.info(f"Session mapping stored/updated: user_id={user_id}, session_id={session_id}")
        except Exception as e:
            logger.error(f"Error storing session mapping: {str(e)}")
            raise


async def store_message(user_id, session_id, role, content):
    """Store message in the database."""
    logger.debug(f"Storing message: user_id={user_id}, session_id={session_id}, role={role}")
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute('''
            INSERT INTO messages (user_id, session_id, role, content)
            VALUES ($1, $2, $3, $4)
            ''', user_id, session_id, role, content)
            logger.debug(f"Message stored successfully")
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            # Continue execution even if message storage fails


async def session_exists(user_id, session_id):
    """Check if session exists in the database."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.fetchval('''
            SELECT id FROM user_sessions
            WHERE user_id = $1 AND session_id = $2
            ''', user_id, session_id)
            return result is not None
        except Exception as e:
            logger.error(f"Error checking session existence: {str(e)}")
            return False


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
        await store_user(userinfo)

        backend_token = jwt.encode({
            "sub": userinfo["email"],
            "name": userinfo["name"],
            "picture": userinfo.get("picture"),
            "exp": (datetime.utcnow() + timedelta(hours=8)).timestamp()
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)

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


logger.info("Initializing agent configuration")

# First priority: Get AGENT_ENGINE_ID from environment variable
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID", "")
logger.info(f"From environment: AGENT_ENGINE_ID={AGENT_ENGINE_ID}")

# Second priority: Read from deployed agent_resource.txt file
if not AGENT_ENGINE_ID:
    # The agent_resource.txt is placed in this location by the deployment workflow
    resource_path = "./agents/ai-consultant-agent/deployment/agent_resource.txt"
    if os.path.exists(resource_path):
        try:
            with open(resource_path, "r") as f:
                AGENT_ENGINE_ID = f.read().strip()
            logger.info(f"Loaded AGENT_ENGINE_ID from {resource_path}: {AGENT_ENGINE_ID}")
        except Exception as e:
            logger.error(f"Error reading agent resource file: {str(e)}")

# Agent configuration
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_ENGINE_ID_ONLY = AGENT_ENGINE_ID.split('/')[-1]
REASONING_ENGINE_APP_NAME = AGENT_ENGINE_ID_ONLY

# Initialize session service
try:
    session_service = VertexAiSessionService(project=PROJECT_ID, location=LOCATION)
    logger.info("Successfully initialized VertexAiSessionService")
except Exception as e:
    logger.error(f"Failed to initialize VertexAiSessionService: {str(e)}")
    raise

# Auth configuration
bearer_scheme = HTTPBearer()


def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.on_event("startup")
async def startup():
    """Initialize the database pool on startup."""
    try:
        await get_db_pool()
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {str(e)}")
        # Continue startup even if DB fails, to allow health checks


@app.on_event("shutdown")
async def shutdown():
    """Close the database pool on shutdown."""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")


@app.get("/")
def read_root():
    logger.info("Root endpoint called")
    return {
        "message": "Server is running",
        "agent_engine_id": AGENT_ENGINE_ID,
        "word_by_word_streaming": ENABLE_WORD_BY_WORD_STREAMING,
        "database": "PostgreSQL"
    }


# Dedicated health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    """
    Health check endpoint for Cloud Run.
    Returns 200 OK if the server is running and all dependencies are healthy.
    """
    logger.debug("Health check endpoint called")

    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("VERSION", "development"),
        "checks": {
            "server": "ok",
            "database": "ok",
            "agent": "ok"
        }
    }

    # Check database connection with PostgreSQL
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["checks"]["database"] = "failed"
        health_status["status"] = "degraded"

    # Check agent configuration
    if not AGENT_ENGINE_ID:
        logger.warning("Agent Engine ID is not configured")
        health_status["checks"]["agent"] = "warning"
        health_status["status"] = "degraded"

    # Return appropriate HTTP status based on overall health
    if health_status["status"] == "ok":
        return health_status
    else:
        return JSONResponse(
            status_code=200,  # Still return 200 to avoid immediate termination
            content=health_status
        )


def get_agent():
    logger.debug("Getting ReasoningEngine instance")
    try:
        agent = reasoning_engines.ReasoningEngine(AGENT_ENGINE_ID)
        logger.debug("Successfully obtained ReasoningEngine instance")
        return agent
    except Exception as e:
        logger.error(f"Failed to get ReasoningEngine instance: {str(e)}", exc_info=True)
        raise


@app.post("/consult")
async def consult(
        request: Request,
        token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        session_id: Optional[str] = Header(None, alias="session_id")
):
    request_id = os.urandom(4).hex()
    logger.info(f"[{request_id}] === Starting /consult request ===")

    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload["sub"]
    except Exception as e:
        logger.error(f"[{request_id}] JWT decode failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"[{request_id}] Failed to parse request body: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid request body")

    user_input = data.get("prompt", "")
    file_content = data.get("file_content", "")

    # Get the agent
    try:
        agent = get_agent()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")

    # Session management
    if not session_id:
        try:
            vertex_session = agent.create_session(user_id=user_id)
            session_id = vertex_session["id"]
            user_id = vertex_session["user_id"]
            await store_session_mapping(user_id, session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create new session: {str(e)}")
    else:
        if not await session_exists(user_id, session_id):
            await store_session_mapping(user_id, session_id)

    # Store user message
    await store_message(user_id, session_id, "user", user_input)

    # Choose streaming mode based on configuration
    async def generate_streaming_response():
        full_response = ""

        try:
            if ENABLE_WORD_BY_WORD_STREAMING:
                # Word-by-word streaming
                chunk_buffer = ""
                word_count = 0

                for event in agent.stream_query(
                        user_id=user_id,
                        session_id=session_id,
                        message=user_input
                ):
                    for part in event.get("content", {}).get("parts", []):
                        if "text" in part:
                            chunk = part["text"]
                            chunk_buffer += chunk

                            # Split by spaces to get words
                            words = chunk_buffer.split()

                            # Process complete words (all except potentially incomplete last word)
                            for i, word in enumerate(words):
                                # Skip processing the last word if buffer doesn't end with space
                                # This avoids the duplicate word issue
                                if i == len(words) - 1 and not chunk_buffer.endswith(' '):
                                    # Keep the potentially incomplete word in buffer
                                    chunk_buffer = word
                                    break

                                word_count += 1
                                full_response += word + " "

                                # Send word as SSE
                                word_with_space = word + " "
                                sse_data = f"data: {word_with_space}\n\n"
                                yield sse_data

                                # Variable delay based on word length
                                if len(word) > 8:
                                    word_delay = 0.2
                                elif len(word) > 4:
                                    word_delay = 0.15
                                else:
                                    word_delay = 0.1

                                # Pause longer at sentence boundaries
                                if any(char in word for char in '.!?'):
                                    word_delay = 0.4

                                await asyncio.sleep(word_delay)

                            # If buffer ends with space, we've processed all words
                            if chunk_buffer.endswith(' '):
                                chunk_buffer = ""

                # Process any remaining text in buffer
                if chunk_buffer:
                    full_response += chunk_buffer + " "
                    sse_data = f"data: {chunk_buffer} \n\n"
                    yield sse_data
                    await asyncio.sleep(0.1)

            else:
                # Chunk-based streaming (original behavior)
                for event in agent.stream_query(
                        user_id=user_id,
                        session_id=session_id,
                        message=user_input
                ):
                    for part in event.get("content", {}).get("parts", []):
                        if "text" in part:
                            chunk = part["text"]
                            full_response += chunk
                            sse_data = f"data: {chunk}\n\n"
                            yield sse_data
                            await asyncio.sleep(0.01)

            # Send session_id and final marker
            session_data = f"data: {{\"session_id\": \"{session_id}\"}}\n\n"
            yield session_data

            final_marker = "data: [DONE]\n\n"
            yield final_marker

            # Store the complete response
            await store_message(user_id, session_id, "agent", full_response.strip())

        except Exception as e:
            logger.error(f"[{request_id}] Error in streaming response: {str(e)}", exc_info=True)
            error_data = f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            yield error_data
            yield "data: [DONE]\n\n"

    # Return streaming response
    return StreamingResponse(
        generate_streaming_response(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        }
    )


@app.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch('''
        SELECT session_id, created_at, last_used_at 
        FROM user_sessions 
        WHERE user_id = $1 
        ORDER BY last_used_at DESC
        ''', user_id)

    sessions = []
    for row in rows:
        sessions.append({
            "session_id": row['session_id'],
            "user_id": user_id,
            "created_at": row['created_at'].isoformat() if row['created_at'] else None,
            "last_used_at": row['last_used_at'].isoformat() if row['last_used_at'] else None
        })

    if not sessions:
        raise HTTPException(status_code=404, detail=f"No sessions found for user {user_id}")

    return {"user_id": user_id, "sessions": sessions}


@app.get("/history/{user_id}/{session_id}")
async def get_session_history(user_id: str, session_id: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch('''
        SELECT role, content, timestamp 
        FROM messages 
        WHERE user_id = $1 AND session_id = $2 
        ORDER BY timestamp ASC
        ''', user_id, session_id)

    history = []
    for row in rows:
        history.append({
            "role": row['role'],
            "message": row['content'],
            "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None
        })

    if not history:
        raise HTTPException(status_code=404, detail=f"No history found for session {session_id}")

    return {
        "user_id": user_id,
        "session_id": session_id,
        "history": history
    }


@app.delete("/sessions/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    try:
        # Delete from ADK
        session_service.delete_session(
            app_name=REASONING_ENGINE_APP_NAME,
            user_id=user_id,
            session_id=session_id
        )

        # Delete from database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Use a transaction to ensure both deletions happen or neither does
            async with conn.transaction():
                await conn.execute(
                    "DELETE FROM user_sessions WHERE user_id = $1 AND session_id = $2",
                    user_id, session_id
                )

                await conn.execute(
                    "DELETE FROM messages WHERE user_id = $1 AND session_id = $2",
                    user_id, session_id
                )

        return {"message": f"Session {session_id} for user {user_id} deleted successfully"}

    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)