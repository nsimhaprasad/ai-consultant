import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Set environment
from baid_server.config import set_environment_from_args
set_environment_from_args()

# Configure logging
from baid_server.utils.logging import configure_logging, get_logger, CORSMiddlewareLogging
configure_logging()
logger = get_logger()

# Configure settings
from baid_server.config import settings
settings.print_variables()

from baid_server.api.routes import auth, agent, sessions, waitlist, api_key, auth_api_key, ci_error, tenant
from baid_server.api.middleware import TokenLimitMiddleware

from baid_server.api.routes import auth, agent, sessions, waitlist, api_key, auth_api_key, ci_error, users, tenant
from baid_server.db.database import get_db_pool, close_db_pool
from baid_server.services.service_factory import ServiceFactory

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
    title = settings.APP_NAME,
    description = settings.DESCRIPTION,
    version = settings.APP_VERSION,
    lifespan = lifespan
)

# Enable word-by-word streaming logging
ENABLE_WORD_BY_WORD_STREAMING = os.getenv("ENABLE_WORD_BY_WORD_STREAMING", "true").lower() == "true"
logger.info(f"Word-by-word streaming: {'ENABLED' if ENABLE_WORD_BY_WORD_STREAMING else 'DISABLED'}")

## Middlewares ##
# Add CORS logging middleware
app.add_middleware(CORSMiddlewareLogging)

# CORS middleware for the application
app.add_middleware(
    middleware_class=CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add token limit middleware
app.add_middleware(TokenLimitMiddleware)


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
app.include_router(api_key)
app.include_router(auth_api_key)
app.include_router(ci_error)
app.include_router(tenant)
app.include_router(users)

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Application entry point
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("baid_server.main:app", host="0.0.0.0", port=port, reload=True)
