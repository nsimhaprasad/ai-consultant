"""User repository for database operations."""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

import asyncpg

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self._db_pool = db_pool

    async def _get_pool(self):
        """Get the database pool."""
        from baid_server.db.database import get_db_pool
        if not self._db_pool:
            self._db_pool = await get_db_pool()
        return self._db_pool

    async def store_user(self, userinfo: Dict[str, Any], tenant_id: Optional[UUID] = None):
        """Store a user in the database."""
        email = userinfo.get("email")
        name = userinfo.get("name")
        picture = userinfo.get("picture")

        # If no tenant_id is provided, use the default tenant
        if tenant_id is None:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                tenant_id = await conn.fetchval('''
                SELECT id FROM tenants WHERE slug = 'default'
                ''')

        pool = await self._get_pool()
        async with pool.acquire() as conn:
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

    async def add_to_waitlist(
            self,
            email: str,
            name: Optional[str],
            role: Optional[str],
            referral_source: Optional[str],
            ip_address: str
    ):
        """Add a user to the waitlist."""
        pool = await self._get_pool()
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

    async def store_api_key(self, user_id: str, api_key: str, name: str, tenant_id: Optional[UUID] = None, expires_at=None):
        """Store a new API key for a user."""
        # If no tenant_id is provided, get the user's tenant
        if tenant_id is None:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                tenant_id = await conn.fetchval('''
                SELECT tenant_id FROM users WHERE email = $1
                ''', user_id)

        pool = await self._get_pool()
        async with pool.acquire() as conn:
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
        
        pool = await self._get_pool()
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
            
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute(query, *params)

    async def validate_api_key(self, api_key: str):
        """Validate an API key and return user info if valid."""
        pool = await self._get_pool()
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
        pool = await self._get_pool()
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
