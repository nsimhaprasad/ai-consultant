"""API routes for tenant management."""
from typing import List, Optional
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from baid_server.api.dependencies import get_current_user
from baid_server.db.database import get_db_pool
from baid_server.db.repositories.tenant_repository import TenantRepository
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.models.tenant import TenantCreate, TenantResponse
from baid_server.models.user import UserInfo
from baid_server.services.tenant_service import TenantService
from baid_server.services.dependencies import get_tenant_service

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


# Removed local get_tenant_repository and get_user_repository functions
# These are now handled by centralized dependencies in db.dependencies.py
# and consumed by service dependencies in services.dependencies.py

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: dict = Depends(get_current_user), # Kept for potential future use in service
    service: TenantService = Depends(get_tenant_service),
):
    """Create a new tenant."""
    # current_user can be passed to service method if needed for authorization
    return await service.create_tenant(tenant_data=tenant_data)


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    current_user: dict = Depends(get_current_user), # Kept
    service: TenantService = Depends(get_tenant_service),
):
    """List all tenants."""
    return await service.list_tenants()


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    current_user: dict = Depends(get_current_user), # Kept
    service: TenantService = Depends(get_tenant_service),
):
    """Get a tenant by ID."""
    return await service.get_tenant(tenant_id=tenant_id)

@router.get("/{tenant_id}/users", response_model=List[UserInfo])
async def get_tenant_users(
    tenant_id: UUID,
    current_user: dict = Depends(get_current_user), # Kept
    service: TenantService = Depends(get_tenant_service),
):
    """Get all users for a specific tenant."""
    return await service.get_tenant_users(tenant_id=tenant_id)
