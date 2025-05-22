"""Tenant repository for database operations."""
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

import asyncpg

logger = logging.getLogger(__name__)


class TenantRepository:
    """Repository for tenant-related database operations."""

    def __init__(self, db_pool: asyncpg.Pool):
        self._db_pool = db_pool

    async def create_tenant(self, name: str, slug: str) -> UUID:
        """Create a new tenant."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            try:
                tenant_id = await conn.fetchval('''
                INSERT INTO tenants (name, slug)
                VALUES ($1, $2)
                RETURNING id
                ''', name, slug)
                
                logger.info(f"Created tenant: {name} (ID: {tenant_id})")
                return tenant_id
            except Exception as e:
                logger.error(f"Error creating tenant: {str(e)}")
                raise

    async def get_tenant_by_id(self, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a tenant by ID."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow('''
            SELECT id, name, slug, created_at, updated_at
            FROM tenants
            WHERE id = $1
            ''', str(tenant_id))
            
            if not row:
                return None
                
            return {
                "id": row["id"],
                "name": row["name"],
                "slug": row["slug"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    async def get_tenant_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get a tenant by slug."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            row = await conn.fetchrow('''
            SELECT id, name, slug, created_at, updated_at
            FROM tenants
            WHERE slug = $1
            ''', slug)
            
            if not row:
                return None
                
            return {
                "id": UUID(row["id"]),
                "name": row["name"],
                "slug": row["slug"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

    async def list_tenants(self) -> List[Dict[str, Any]]:
        """List all tenants."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            rows = await conn.fetch('''
            SELECT id, name, slug, created_at, updated_at
            FROM tenants
            ORDER BY name
            ''')
            
            tenants = []
            for row in rows:
                tenants.append({
                    "id": row["id"],
                    "name": row["name"],
                    "slug": row["slug"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })
                
            return tenants

    async def update_tenant(self, tenant_id: UUID, name: str, slug: str) -> bool:
        """Update a tenant."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            try:
                result = await conn.execute('''
                UPDATE tenants
                SET name = $2, slug = $3, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                ''', str(tenant_id), name, slug)
                
                if result == "UPDATE 0":
                    logger.warning(f"No tenant found with ID: {tenant_id}")
                    return False
                    
                logger.info(f"Updated tenant ID: {tenant_id}")
                return True
            except Exception as e:
                logger.error(f"Error updating tenant: {str(e)}")
                raise

    async def delete_tenant(self, tenant_id: UUID) -> bool:
        """Delete a tenant (will fail if there are associated users or API keys)."""
        pool = self._db_pool
        async with pool.acquire() as conn:
            try:
                result = await conn.execute('''
                DELETE FROM tenants
                WHERE id = $1
                ''', str(tenant_id))
                
                if result == "DELETE 0":
                    logger.warning(f"No tenant found with ID: {tenant_id}")
                    return False
                    
                logger.info(f"Deleted tenant ID: {tenant_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting tenant: {str(e)}")
                raise
