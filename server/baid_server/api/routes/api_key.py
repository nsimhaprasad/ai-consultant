import logging
import os
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from fastapi.responses import JSONResponse

from baid_server.api.dependencies import get_current_user
from baid_server.db.database import get_db_pool
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.models.api_key import ApiKeyCreate, ApiKeyResponse

router = APIRouter(prefix="/api/keys", tags=["api_keys"])
logger = logging.getLogger(__name__)


async def get_user_repository():
    """Dependency to get the user repository."""
    return UserRepository(db_pool=await get_db_pool())


@router.post("", response_model=dict)
async def create_api_key(
        api_key_data: ApiKeyCreate,
        current_user: Dict[str, Any] = Depends(get_current_user),
        user_repository: UserRepository = Depends(get_user_repository),
):
    """Create a new API key for the authenticated user."""
    user_id = current_user["sub"]
    
    # Generate a new API key with a prefix
    key_prefix = "baid_"
    api_key = f"{key_prefix}{secrets.token_hex(24)}"
    
    try:
        # Store the API key
        key_id = await user_repository.store_api_key(
            user_id=user_id,
            api_key=api_key,
            name=api_key_data.name,
            tenant_id=api_key_data.tenant_id,
            expires_at=(datetime.now() + timedelta(days=api_key_data.expiry_days)) if api_key_data.expiry_days else None
        )
        
        return {
            "key_id": key_id,
            "api_key": api_key,  # Only shown once at creation time
            "name": api_key_data.name,
            "tenant_id": api_key_data.tenant_id,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(
                days=api_key_data.expiry_days)).isoformat() if api_key_data.expiry_days else None
        }
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
        current_user: Dict[str, Any] = Depends(get_current_user),
        user_repository: UserRepository = Depends(get_user_repository),
        tenant_id: Optional[UUID] = Query(None, description="Filter keys by tenant ID")
):
    """List all API keys for the authenticated user."""
    user_id = current_user["sub"]
    try:
        keys = await user_repository.get_user_api_keys(user_id, tenant_id)
        return keys
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve API keys: {str(e)}"
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
        key_id: str = Path(..., description="ID of the API key to delete"),
        current_user: Dict[str, Any] = Depends(get_current_user),
        user_repository: UserRepository = Depends(get_user_repository),
        tenant_id: Optional[UUID] = Query(None, description="Tenant ID for the key")
):
    """Delete an API key."""
    user_id = current_user["sub"]
    try:
        await user_repository.delete_api_key(user_id, key_id, tenant_id)
        return {"message": "API key deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}"
        )