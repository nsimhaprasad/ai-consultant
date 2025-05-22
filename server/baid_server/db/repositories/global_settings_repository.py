"""Global settings repository for database operations."""
import logging
from typing import Optional, Any

import asyncpg

logger = logging.getLogger(__name__)


class GlobalSettingsRepository:
    """Repository for global settings related database operations."""

    def __init__(self, db_pool: asyncpg.Pool):
        self._db_pool = db_pool

    async def update_setting(self, setting_key: str, setting_value: str) -> None:
        """Insert or update a global setting."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO global_settings (setting_key, setting_value, updated_at)
                    VALUES ($1, $2, CURRENT_TIMESTAMP)
                    ON CONFLICT (setting_key) DO UPDATE SET
                        setting_value = $2,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    setting_key, setting_value
                )
                logger.info(f"Global setting {setting_key} updated to {setting_value}")
            except Exception as e:
                logger.error(f"Error updating global setting {setting_key}: {str(e)}")
                raise

    async def get_setting(self, setting_key: str) -> Optional[Dict[str, Any]]:
        """Get a global setting by key."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    "SELECT setting_key, setting_value, updated_at FROM global_settings WHERE setting_key = $1",
                    setting_key
                )
                if row:
                    return dict(row)
                return None
            except Exception as e:
                logger.error(f"Error fetching global setting {setting_key}: {str(e)}")
                raise # Or return None / handle as per desired error strategy
    
    async def get_default_token_limit(self) -> Optional[int]:
        """Convenience method to get the default token limit."""
        setting = await self.get_setting('default_token_limit')
        if setting and setting.get('setting_value'):
            try:
                return int(setting['setting_value'])
            except ValueError:
                logger.error(f"Default token limit value '{setting['setting_value']}' is not a valid integer.")
                return None
        return None

    async def update_default_token_limit(self, token_limit: int) -> None:
        """Convenience method to update the default token limit."""
        await self.update_setting('default_token_limit', str(token_limit))
