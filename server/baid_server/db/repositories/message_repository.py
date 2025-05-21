"""Message repository for database operations."""
import logging
from typing import List, Dict, Any, Optional

import asyncpg

from baid_server.db.database import get_db_pool

logger = logging.getLogger(__name__)


class MessageRepository:

    def __init__(self, db_pool: asyncpg.Pool): # Modified: db_pool is now required
        self._db_pool = db_pool
    
    # Removed _get_pool method

    async def store_message(self, user_id: str, session_id: str, role: str, content: str) -> None:
        logger.debug(f"Storing message: user_id={user_id}, session_id={session_id}, role={role}")
        pool = self._db_pool # Modified: Use self._db_pool directly
        async with pool.acquire() as conn:
            try:
                await conn.execute('''
                INSERT INTO messages (user_id, session_id, role, content)
                VALUES ($1, $2, $3, $4)
                ''', user_id, session_id, role, content)
                logger.debug("Message stored successfully")
            except Exception as e:
                logger.error(f"Error storing message: {str(e)}")
                # Continue execution even if message storage fails


    async def get_session_history(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        pool = self._db_pool # Modified: Use self._db_pool directly
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
        
        return history
