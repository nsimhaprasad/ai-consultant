"""Service layer for tenant management."""
import logging
from typing import List
from uuid import UUID

from fastapi import HTTPException, status

from baid_server.db.repositories.tenant_repository import TenantRepository
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.models.tenant import TenantCreate, TenantResponse
from baid_server.models.user import UserInfo

logger = logging.getLogger(__name__)


class TenantService:
    """Service for tenant-related operations."""

    def __init__(self, tenant_repo: TenantRepository, user_repo: UserRepository):
        self._tenant_repo = tenant_repo
        self._user_repo = user_repo

    async def create_tenant(self, tenant_data: TenantCreate) -> TenantResponse:
        """Create a new tenant."""
        try:
            # In a real application, you might want to check if the user has permission to create tenants
            # For now, directly creating.
            # Also, consider if slug needs to be auto-generated or validated for uniqueness more robustly.
            tenant_id = await self._tenant_repo.create_tenant(
                name=tenant_data.name,
                slug=tenant_data.slug,
            )
            
            tenant = await self._tenant_repo.get_tenant_by_id(tenant_id)
            if not tenant:
                # This case should ideally not happen if create_tenant returns a valid ID
                logger.error(f"Tenant created with ID {tenant_id} but not found immediately after.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Tenant created but could not be retrieved.",
                )
            return TenantResponse(**tenant)
        except Exception as e:
            logger.error(f"Error creating tenant in service: {str(e)}")
            # Re-raise as HTTPException or handle specific exceptions
            if isinstance(e, HTTPException):
                raise
            # Check for specific database errors, e.g., unique constraint violation for slug
            # For now, a generic error for unhandled exceptions
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # Or 500 if it's an internal error
                detail=f"Failed to create tenant: {str(e)}",
            )

    async def list_tenants(self) -> List[TenantResponse]:
        """List all tenants."""
        try:
            tenants = await self._tenant_repo.list_tenants()
            return [TenantResponse(**tenant) for tenant in tenants]
        except Exception as e:
            logger.error(f"Error listing tenants in service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list tenants.",
            )

    async def get_tenant(self, tenant_id: UUID) -> TenantResponse:
        """Get a tenant by ID."""
        tenant = await self._tenant_repo.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with ID {tenant_id} not found",
            )
        return TenantResponse(**tenant)

    async def get_tenant_users(self, tenant_id: UUID) -> List[UserInfo]:
        """Get all users for a specific tenant."""
        # First, check if tenant exists to provide a clear 404 if not
        tenant = await self._tenant_repo.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant with ID {tenant_id} not found, cannot list users.",
            )
        
        try:
            users = await self._user_repo.get_users_by_tenant(tenant_id)
            return [UserInfo(**user) for user in users]
        except Exception as e:
            logger.error(f"Error getting tenant users in service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve users for tenant {tenant_id}.",
            )
