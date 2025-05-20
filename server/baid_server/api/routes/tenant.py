"""API routes for tenant management."""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from baid_server.api.dependencies import get_current_user
from baid_server.db.repositories.tenant_repository import TenantRepository
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.models.tenant import TenantCreate, TenantResponse
from baid_server.models.user import UserInfo

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


async def get_tenant_repository():
    """Dependency to get the tenant repository."""
    return TenantRepository()

async def get_user_repository():
    """Dependency to get the user repository."""
    return UserRepository()

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    current_user: dict = Depends(get_current_user),
    tenant_repository: TenantRepository = Depends(get_tenant_repository),
):
    """Create a new tenant."""
    # In a real application, you might want to check if the user has permission to create tenants
    try:
        tenant_id = await tenant_repository.create_tenant(
            name=tenant_data.name,
            slug=tenant_data.slug,
        )
        
        tenant = await tenant_repository.get_tenant_by_id(tenant_id)
        return TenantResponse(**tenant)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create tenant: {str(e)}",
        )


@router.get("", response_model=List[TenantResponse])
async def list_tenants(
    current_user: dict = Depends(get_current_user),
    tenant_repository: TenantRepository = Depends(get_tenant_repository),
):
    """List all tenants."""
    # In a real application, you might want to filter tenants based on user permissions
    tenants = await tenant_repository.list_tenants()
    return [TenantResponse(**tenant) for tenant in tenants]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    current_user: dict = Depends(get_current_user),
    tenant_repository: TenantRepository = Depends(get_tenant_repository),
):
    """Get a tenant by ID."""
    tenant = await tenant_repository.get_tenant_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {tenant_id} not found",
        )
    return TenantResponse(**tenant)

@router.get("/{tenant_id}/users", response_model=List[UserInfo])
async def get_tenant_users(
    tenant_id: UUID,
    current_user: dict = Depends(get_current_user),
    user_repository: UserRepository = Depends(get_user_repository)
):
    """Get a tenant by ID."""
    users = await user_repository.get_users_by_tenant(tenant_id)
    return [UserInfo(**user) for user in users]
