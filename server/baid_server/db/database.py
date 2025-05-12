"""Database connection management."""
import logging
import os
from typing import Optional

import asyncpg
from google.cloud import secretmanager

logger = logging.getLogger(__name__)

# DB configuration
DB_CONNECTION_SECRET = os.environ.get("DB_CONNECTION_SECRET", "postgres-connection")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "ai_consultant_db")
DB_USER = os.environ.get("DB_USER", "baid-dev")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
PROJECT_ID = os.getenv("PROJECT_ID", "742371152853")

# Global connection pool
db_pool: Optional[asyncpg.Pool] = None


async def get_secret(secret_id: str) -> str:
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


async def get_db_pool() -> asyncpg.Pool:
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


async def close_db_pool():
    """Close the database connection pool."""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")
        db_pool = None
