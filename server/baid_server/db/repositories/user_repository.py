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
