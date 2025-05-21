"""Waitlist repository for database operations."""
import logging
from typing import Optional

import asyncpg

logger = logging.getLogger(__name__)


class WaitlistRepository:
    """Repository for waitlist-related database operations."""

    def __init__(self, db_pool: asyncpg.Pool):
        self._db_pool = db_pool

    async def add_to_waitlist(
            self,
            email: str,
            name: Optional[str],
            role: Optional[str],
            referral_source: Optional[str],
            ip_address: str
    ):
        """Add a user to the waitlist."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            try:
                await conn.execute('''
                INSERT INTO waitlist (email, name, role, referral_source, ip_address)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (email) DO NOTHING
                ''', email, name, role, referral_source, ip_address)

                logger.info(f"Added to waitlist: {email}")
            except Exception as e:
                logger.error(f"Error adding to waitlist: {str(e)}")
                raise
