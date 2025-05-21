"""Centralized dependency providers for database repositories."""
import asyncpg
from fastapi import Depends

from baid_server.db.database import get_db_pool
from baid_server.db.repositories.tenant_repository import TenantRepository
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.db.repositories.message_repository import MessageRepository
from baid_server.db.repositories.session_repository import SessionRepository
from baid_server.db.repositories.waitlist_repository import WaitlistRepository
from baid_server.db.repositories.global_settings_repository import GlobalSettingsRepository


# Removed get_db_pool_dependency as it's redundant.
# Repository providers will directly use Depends(get_db_pool).

async def get_tenant_repository_dependency(
    pool: asyncpg.Pool = Depends(get_db_pool) 
) -> TenantRepository:
    """Dependency to get the TenantRepository instance."""
    return TenantRepository(db_pool=pool)


async def get_user_repository_dependency(
    pool: asyncpg.Pool = Depends(get_db_pool)
) -> UserRepository:
    """Dependency to get the UserRepository instance."""
    return UserRepository(db_pool=pool)


async def get_message_repository_dependency(
    pool: asyncpg.Pool = Depends(get_db_pool)
) -> MessageRepository: 
    """Dependency to get the MessageRepository instance."""
    return MessageRepository(db_pool=pool)


async def get_session_repository_dependency(
    pool: asyncpg.Pool = Depends(get_db_pool)
) -> SessionRepository: 
    """Dependency to get the SessionRepository instance."""
    return SessionRepository(db_pool=pool)

async def get_waitlist_repository_dependency(
    pool: asyncpg.Pool = Depends(get_db_pool)
) -> WaitlistRepository: 
    """Dependency to get the WaitlistRepository instance."""
    return WaitlistRepository(db_pool=pool)

async def get_global_settings_repository_dependency(
    pool: asyncpg.Pool = Depends(get_db_pool)
) -> GlobalSettingsRepository: 
    """Dependency to get the GlobalSettingsRepository instance."""
    return GlobalSettingsRepository(db_pool=pool)
