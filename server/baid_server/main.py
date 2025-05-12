import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from baid_server.api.routes import auth, agent, sessions, waitlist
from baid_server.db.database import get_db_pool, close_db_pool
from baid_server.services.service_factory import ServiceFactory

# Load environment variables
dotenv.load_dotenv()

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("adk_server")


# Create FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Initialize database connection pool
        await get_db_pool()
        logger.info("Database connection pool initialized")

        # Initialize agent service
        await ServiceFactory.initialize_agent_service()
        yield
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        yield
    finally:
        # Cleanup on shutdown
        try:
            await close_db_pool()
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


app = FastAPI(
    title="BAID Server",
    description="AI Consultant API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable word-by-word streaming logging
ENABLE_WORD_BY_WORD_STREAMING = os.getenv("ENABLE_WORD_BY_WORD_STREAMING", "true").lower() == "true"
logger.info(f"Word-by-word streaming: {'ENABLED' if ENABLE_WORD_BY_WORD_STREAMING else 'DISABLED'}")

# CORS middleware for the application
app.add_middleware(
    middleware_class=CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    logger.info("Root endpoint called")

    return {
        "message": "Server is running",
        "agent_engine_id": os.getenv("AGENT_ENGINE_ID", ""),
        "word_by_word_streaming": os.getenv("ENABLE_WORD_BY_WORD_STREAMING", "true").lower() == "true",
        "database": "PostgreSQL"
    }


# Dedicated health check endpoint for Cloud Run
@app.get("/health")
async def health_check():
    logger.debug("Health check endpoint called")

    health_status = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": os.getenv("VERSION", "development"),
        "checks": {
            "server": "ok",
            "database": "ok",
            "agent": "ok"
        }
    }

    # Check database connection with Postgres SQL
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["checks"]["database"] = "failed"
        health_status["status"] = "degraded"

    # Check agent configuration
    if not os.getenv("AGENT_ENGINE_ID", ""):
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


# Register routers
app.include_router(auth)
app.include_router(agent)
app.include_router(sessions)
app.include_router(waitlist)

# Application entry point
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("baid_server.main:app", host="0.0.0.0", port=port, reload=True)
