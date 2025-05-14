"""User repository for database operations."""
import logging
from typing import Dict, Any, Optional

import asyncpg

from baid_server.db.database import get_db_pool

logger = logging.getLogger(__name__)


class UserRepository:

    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self._db_pool = db_pool

    async def _get_pool(self) -> asyncpg.Pool:
        if self._db_pool is None:
            return await get_db_pool()
        return self._db_pool

    async def store_user(self, userinfo: Dict[str, Any]) -> None:
        pool = await self._get_pool()
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

    async def add_to_waitlist(
            self,
            email: str,
            name: Optional[str],
            role: Optional[str],
            referral_source: Optional[str],
            ip_address: str
    ) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                await conn.execute('''
                INSERT INTO waitlist (email, name, role, referral_source, ip_address)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (email) 
                DO UPDATE SET 
                    name = COALESCE($2, waitlist.name),
                    role = COALESCE($3, waitlist.role),
                    referral_source = COALESCE($4, waitlist.referral_source),
                    ip_address = $5
                ''', email, name, role, referral_source, ip_address)

                logger.info(f"User added to waitlist: {email} (IP: {ip_address})")
            except Exception as e:
                logger.error(f"Error adding user to waitlist: {str(e)}")
                raise

    """
    Extensions to UserRepository for API key management.
    These methods should be added to the existing UserRepository class.
    """

    async def store_api_key(self, user_id: str, api_key: str, name: str, expires_at=None):
        """Store a new API key for a user."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            try:
                result = await conn.fetchval('''
                INSERT INTO api_keys (user_id, api_key, name, expires_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                ''', user_id, api_key, name, expires_at)

                logger.info(f"API key stored for user: {user_id}")
                return str(result)
            except Exception as e:
                logger.error(f"Error storing API key: {str(e)}")
                raise

    async def get_user_api_keys(self, user_id: str):
        """Get all API keys for a user (excluding the actual key values)."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch('''
            SELECT id, name, created_at, expires_at 
            FROM api_keys 
            WHERE user_id = $1 AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            ''', user_id)

        keys = []
        for row in rows:
            keys.append({
                "key_id": str(row['id']),
                "name": row['name'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None
            })

        return keys

    async def delete_api_key(self, user_id: str, key_id: str):
        """Delete an API key."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute('''
            DELETE FROM api_keys 
            WHERE id = $1 AND user_id = $2
            ''', key_id, user_id)

    async def validate_api_key(self, api_key: str):
        """Validate an API key and return user info if valid."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Find the API key and join with users table to get user info
            row = await conn.fetchrow('''
            SELECT u.email, u.name, k.user_id
            FROM api_keys k
            JOIN users u ON k.user_id = u.email
            WHERE k.api_key = $1 
              AND (k.expires_at IS NULL OR k.expires_at > NOW())
            ''', api_key)

        if row:
            return {
                "user_id": row['user_id'],
                "email": row['email'],
                "name": row['name']
            }
        return None
