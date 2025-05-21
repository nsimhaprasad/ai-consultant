"""User repository for database operations."""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

import asyncpg

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, db_pool: asyncpg.Pool):
        self._db_pool = db_pool

    async def store_user(self, userinfo: Dict[str, Any], tenant_id: Optional[UUID] = None):
        """Store a user in the database."""
        email = userinfo.get("email")
        name = userinfo.get("name")
        picture = userinfo.get("picture")

        pool = self._db_pool # Use self._db_pool directly

        # If no tenant_id is provided, use the default tenant
        if tenant_id is None:
            async with pool.acquire() as conn: # Use acquired connection from self._db_pool
                tenant_id = await conn.fetchval('''
                SELECT id FROM tenants WHERE slug = 'default'
                ''')

        async with pool.acquire() as conn: # Use acquired connection from self._db_pool
            try:
                await conn.execute('''
                INSERT INTO users (email, name, picture, tenant_id)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (email) DO UPDATE
                SET name = $2, picture = $3
                ''', email, name, picture, str(tenant_id) if tenant_id else None)

                logger.info(f"User stored: {email}")
            except Exception as e:
                logger.error(f"Error storing user: {str(e)}")
                raise

    # add_to_waitlist method removed from UserRepository

    async def update_user_status(self, user_id: str, status: str) -> bool:
        """Insert or update a user's status."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            # Check if user exists
            user_exists = await conn.fetchval("SELECT 1 FROM users WHERE email = $1", user_id)
            if not user_exists:
                logger.warning(f"User {user_id} not found for status update.")
                return False
            
            await conn.execute(
                """
                INSERT INTO user_status (user_id, status, updated_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    status = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, status
            )
            logger.info(f"Updated status for user {user_id} to {status}")
            return True

    async def get_user_status(self, user_id: str) -> Optional[str]:
        """Get a user's status."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            status = await conn.fetchval("SELECT status FROM user_status WHERE user_id = $1", user_id)
            return status

    async def update_user_token_limit(self, user_id: str, token_limit: int) -> bool:
        """Insert or update a user's token limit."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            user_exists = await conn.fetchval("SELECT 1 FROM users WHERE email = $1", user_id)
            if not user_exists:
                logger.warning(f"User {user_id} not found for token limit update.")
                return False

            await conn.execute(
                """
                INSERT INTO user_settings (user_id, setting_key, setting_value, updated_at)
                VALUES ($1, 'token_limit', $2, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, setting_key) DO UPDATE SET
                    setting_value = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, str(token_limit)
            )
            logger.info(f"Updated token limit for user {user_id} to {token_limit}")
            return True

    async def get_user_token_limit(self, user_id: str) -> Optional[int]:
        """Get a user's token limit."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            limit_str = await conn.fetchval(
                "SELECT setting_value FROM user_settings WHERE user_id = $1 AND setting_key = 'token_limit'",
                user_id
            )
            if limit_str:
                try:
                    return int(limit_str)
                except ValueError:
                    logger.error(f"Invalid token limit value '{limit_str}' for user {user_id}.")
                    return None
            return None
            
    async def get_dashboard_users_data(self) -> List[Dict[str, Any]]:
        """Fetch comprehensive data for the users dashboard."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            # This query is complex and aggregates data from multiple tables.
            # It's a simplified version of the original dashboard logic.
            # Token count estimation logic (estimate_tokens) would be in the service layer or a utility.
            rows = await conn.fetch("""
                SELECT 
                    u.id, 
                    u.email, 
                    u.name, 
                    u.picture, 
                    u.created_at,
                    COUNT(m.id) as message_count,
                    MAX(m.timestamp) as last_active,
                    us.status as user_status,
                    COALESCE(uset.setting_value, gs.setting_value) as token_limit_value
                FROM users u
                LEFT JOIN messages m ON u.email = m.user_id
                LEFT JOIN user_status us ON u.email = us.user_id
                LEFT JOIN user_settings uset ON u.email = uset.user_id AND uset.setting_key = 'token_limit'
                LEFT JOIN global_settings gs ON gs.setting_key = 'default_token_limit'
                GROUP BY u.id, u.email, u.name, u.picture, u.created_at, us.status, uset.setting_value, gs.setting_value
                ORDER BY u.created_at DESC
            """)
            # Further processing (like token estimation, relative time) will be done in the service layer.
            return [dict(row) for row in rows]

    async def store_api_key(self, user_id: str, api_key: str, name: str, tenant_id: Optional[UUID] = None, expires_at=None):
        """Store a new API key for a user."""
        pool = self._db_pool # Use self._db_pool directly

        # If no tenant_id is provided, get the user's tenant
        if tenant_id is None:
            async with pool.acquire() as conn: # Use acquired connection from self._db_pool
                tenant_id = await conn.fetchval('''
                SELECT tenant_id FROM users WHERE email = $1
                ''', user_id)

        async with pool.acquire() as conn: # Use acquired connection from self._db_pool
            try:
                result = await conn.fetchval('''
                INSERT INTO api_keys (user_id, api_key, name, tenant_id, expires_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                ''', user_id, api_key, name, str(tenant_id) if tenant_id else None, expires_at)

                logger.info(f"API key stored for user: {user_id}")
                return str(result)
            except Exception as e:
                logger.error(f"Error storing API key: {str(e)}")
                raise

    async def get_user_api_keys(self, user_id: str, tenant_id: Optional[UUID] = None):
        """Get all API keys for a user (excluding the actual key values)."""
        query = '''
        SELECT id, name, created_at, expires_at 
        FROM api_keys 
        WHERE user_id = $1 AND (expires_at IS NULL OR expires_at > NOW())
        '''
        
        params = [user_id]
        
        if tenant_id is not None:
            query += " AND tenant_id = $2"
            params.append(str(tenant_id))
            
        query += " ORDER BY created_at DESC"
        
        pool = self._db_pool
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

        keys = []
        for row in rows:
            keys.append({
                "key_id": str(row['id']),
                "name": row['name'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "expires_at": row['expires_at'].isoformat() if row['expires_at'] else None
            })

        return keys

    async def delete_api_key(self, user_id: str, key_id: str, tenant_id: Optional[UUID] = None):
        """Delete an API key."""
        query = '''
        DELETE FROM api_keys 
        WHERE id = $1 AND user_id = $2
        '''
        
        params = [key_id, user_id]
        
        if tenant_id is not None:
            query += " AND tenant_id = $3"
            params.append(str(tenant_id))
            
        pool = self._db_pool
        async with pool.acquire() as conn:
            await conn.execute(query, *params)

    async def validate_api_key(self, api_key: str):
        """Validate an API key and return user info if valid."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            # Find the API key and join with users table to get user info
            row = await conn.fetchrow('''
            SELECT u.email, u.name, k.user_id, k.tenant_id, t.name as tenant_name, t.slug as tenant_slug
            FROM api_keys k
            JOIN users u ON k.user_id = u.email
            JOIN tenants t ON k.tenant_id = t.id
            WHERE k.api_key = $1 
              AND (k.expires_at IS NULL OR k.expires_at > NOW())
            ''', api_key)

        if row:
            return {
                "email": row["email"],
                "name": row["name"],
                "user_id": row["user_id"],
                "tenant_id": UUID(row["tenant_id"]),
                "tenant_name": row["tenant_name"],
                "tenant_slug": row["tenant_slug"]
            }
        return None
        
    async def get_users_by_tenant(self, tenant_id: UUID) -> List[Dict[str, Any]]:
        """Get all users belonging to a specific tenant."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            rows = await conn.fetch('''
            SELECT email, name, picture, created_at
            FROM users
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            ''', str(tenant_id))
            
            users = []
            for row in rows:
                users.append({
                    "email": row["email"],
                    "name": row["name"],
                    "picture": row["picture"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None
                })
                
            return users
