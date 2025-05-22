"""Session repository for database operations."""
import logging
from typing import List, Dict, Any, Optional

import asyncpg

from baid_server.db.database import get_db_pool

logger = logging.getLogger(__name__)


class SessionRepository:
    def __init__(self, db_pool: asyncpg.Pool): # Modified: db_pool is now required
        self._db_pool = db_pool
    
    # Removed _get_pool method

    async def store_session_mapping(self, user_id: str, session_id: str) -> None:
        logger.info(f"Storing/updating session mapping: user_id={user_id}, session_id={session_id}")
        pool = self._db_pool # Modified: Use self._db_pool directly
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

    async def session_exists(self, user_id: str, session_id: str) -> bool:
        pool = self._db_pool # Modified: Use self._db_pool directly
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

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        pool = self._db_pool # Modified: Use self._db_pool directly
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
        
        return sessions

    async def delete_session(self, user_id: str, session_id: str) -> None:
        pool = self._db_pool # Modified: Use self._db_pool directly
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
