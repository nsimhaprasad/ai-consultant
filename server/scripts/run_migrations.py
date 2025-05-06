#!/usr/bin/env python
"""
Database migration script to run at container startup.
This script applies SQL migration files from the migrations directory.
"""

import os
import sys
import logging
import time
import asyncio
import asyncpg
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("db_migrations")

# Get database connection details from environment variables
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "ai_consultant_db")
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# For production, we'll use the secret manager
DB_CONNECTION_SECRET = os.environ.get("DB_CONNECTION_SECRET", "")
PROJECT_ID = os.environ.get("PROJECT_ID", "")

# Maximum number of retries for database connection
MAX_RETRIES = 10
RETRY_DELAY = 5  # seconds

# Path to migration files
MIGRATIONS_DIR = Path("/app/migrations")


async def get_connection_string():
    """Get database connection string from environment or Secret Manager."""
    if os.environ.get("ENVIRONMENT") == "development" and DB_PASSWORD:
        # For local development, use env vars
        connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        logger.info("Using local database connection from environment variables")
        return connection_string

    elif DB_CONNECTION_SECRET and PROJECT_ID:
        # For production, get from Secret Manager
        try:
            from google.cloud import secretmanager

            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{PROJECT_ID}/secrets/{DB_CONNECTION_SECRET}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            connection_string = response.payload.data.decode("UTF-8")
            logger.info(f"Using database connection from Secret Manager: {DB_CONNECTION_SECRET}")
            return connection_string
        except Exception as e:
            logger.error(f"Error accessing secret {DB_CONNECTION_SECRET}: {str(e)}")
            raise
    else:
        # Fallback
        connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        logger.warning("No secret manager configuration found, using environment variables")
        return connection_string


async def create_migration_table(conn):
    """Create migration tracking table if it doesn't exist."""
    await conn.execute('''
    CREATE TABLE IF NOT EXISTS migration_history (
        id SERIAL PRIMARY KEY,
        filename TEXT UNIQUE NOT NULL,
        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
    ''')


async def get_applied_migrations(conn):
    """Get list of already applied migrations."""
    return set(row['filename'] for row in await conn.fetch('SELECT filename FROM migration_history'))


async def apply_migrations():
    """Apply all pending migration files."""
    connection_string = await get_connection_string()

    # Try to connect to database with retries
    for attempt in range(MAX_RETRIES):
        try:
            conn = await asyncpg.connect(connection_string)
            logger.info("Successfully connected to the database")
            break
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    f"Database connection attempt {attempt + 1} failed: {str(e)}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to connect to database after {MAX_RETRIES} attempts: {str(e)}")
                return False

    try:
        # Create migration tracking table
        await create_migration_table(conn)

        # Get already applied migrations
        applied_migrations = await get_applied_migrations(conn)

        # Get all migration files
        migration_files = sorted([f for f in MIGRATIONS_DIR.glob('*.sql')])

        if not migration_files:
            logger.warning(f"No migration files found in {MIGRATIONS_DIR}")
            return True

        # Apply pending migrations
        for migration_file in migration_files:
            filename = migration_file.name

            if filename in applied_migrations:
                logger.info(f"Migration {filename} already applied")
                continue

            logger.info(f"Applying migration: {filename}")
            try:
                # Read the migration content
                with open(migration_file, 'r') as f:
                    migration_sql = f.read()

                # Execute the migration in a transaction
                async with conn.transaction():
                    await conn.execute(migration_sql)
                    await conn.execute(
                        'INSERT INTO migration_history (filename) VALUES ($1)',
                        filename
                    )
                logger.info(f"Successfully applied migration: {filename}")
            except Exception as e:
                logger.error(f"Failed to apply migration {filename}: {str(e)}")
                return False

        logger.info("All migrations applied successfully")
        return True

    except Exception as e:
        logger.error(f"Error during migration process: {str(e)}")
        return False
    finally:
        await conn.close()


def main():
    """Run migrations and exit with appropriate status code."""
    success = asyncio.run(apply_migrations())
    if not success:
        logger.error("Migration failed")
        sys.exit(1)
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()