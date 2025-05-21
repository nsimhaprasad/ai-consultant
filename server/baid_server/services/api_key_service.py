"""Service layer for API key management."""
import logging
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status

from baid_server.db.repositories.user_repository import UserRepository
from baid_server.models.api_key import ApiKeyCreate, ApiKeyResponse

logger = logging.getLogger(__name__)


class ApiKeyService:
    """Service for API key related operations."""

    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def create_api_key(
        self, api_key_data: ApiKeyCreate, user_id: str
    ) -> dict: # Returning dict as per current route, includes the raw key
        """Create a new API key for the user."""
        key_prefix = "baid_"
        raw_api_key = f"{key_prefix}{secrets.token_hex(24)}" # Generate the actual secret key

        try:
            expires_at_dt = None
            if api_key_data.expiry_days:
                expires_at_dt = datetime.now() + timedelta(days=api_key_data.expiry_days)

            key_id = await self._user_repo.store_api_key(
                user_id=user_id,
                api_key=raw_api_key, # Store the hashed key if UserRepo handles hashing, or raw if not
                name=api_key_data.name,
                tenant_id=api_key_data.tenant_id,
                expires_at=expires_at_dt,
            )
            
            # The response includes the raw API key, which should only be shown once.
            return {
                "key_id": key_id,
                "api_key": raw_api_key,
                "name": api_key_data.name,
                "tenant_id": str(api_key_data.tenant_id) if api_key_data.tenant_id else None,
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at_dt.isoformat() if expires_at_dt else None,
            }
        except Exception as e:
            logger.error(f"Error creating API key in service for user {user_id}: {str(e)}")
            # Consider specific exceptions, e.g., if tenant_id is invalid
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 400 if bad input
                detail=f"Failed to create API key: {str(e)}",
            )

    async def list_api_keys(
        self, user_id: str, tenant_id: Optional[UUID]
    ) -> List[ApiKeyResponse]:
        """List all API keys for the user, optionally filtered by tenant."""
        try:
            keys_data = await self._user_repo.get_user_api_keys(user_id, tenant_id)
            # Convert to ApiKeyResponse Pydantic models
            return [ApiKeyResponse(**key) for key in keys_data]
        except Exception as e:
            logger.error(f"Error listing API keys in service for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve API keys.",
            )

    async def delete_api_key(
        self, user_id: str, key_id: str, tenant_id: Optional[UUID]
    ) -> None:
        """Delete an API key."""
        try:
            # UserRepository.delete_api_key should handle not found cases,
            # or we can add a check here if needed (e.g., get_api_key_by_id first).
            # For now, assuming the repository handles "not found" gracefully or the controller ensures key ownership.
            await self._user_repo.delete_api_key(user_id, key_id, tenant_id)
            # No return value needed for a successful deletion (204 No Content)
        except Exception as e:
            # This could include errors like "key not found" if not handled by repo,
            # or database errors.
            logger.error(f"Error deleting API key {key_id} for user {user_id} in service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 404 if not found, if known
                detail=f"Failed to delete API key: {str(e)}",
            )
