"""Database connection management."""
import logging
import os
from typing import Optional

import asyncpg
from google.cloud import secretmanager

from baid_server.config import settings

logger = logging.getLogger(__name__)

# DB configuration
# 34.67.106.163
# GZ5NGUHVoP3kkuZuB6Ey
DB_CONNECTION_SECRET = settings.DB_CONNECTION_SECRET
DB_HOST = settings.DB_HOST
DB_PORT = settings.DB_PORT
DB_NAME = settings.DB_NAME
DB_USER = settings.DB_USER
DB_PASSWORD = settings.DB_PASSWORD.get_secret_value() if settings.DB_PASSWORD else None
PROJECT_ID = settings.PROJECT_ID

# Global connection pool
db_pool: Optional[asyncpg.Pool] = None


async def get_secret(secret_id: str) -> str:
    """Get secret from Secret Manager."""

    if os.getenv("ENVIRONMENT", "local") == "local":
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {str(e)}")
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
    try:
        yield db_pool
    finally:
        # Pool closure is typically handled at application shutdown,
        # see main.py lifespan manager.
        pass


async def close_db_pool():
    """Close the database connection pool."""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")
        db_pool = None
