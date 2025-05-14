import logging
import os
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse

from baid_server.api.dependencies import get_current_user
from baid_server.db.database import get_db_pool
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.models.api_key import ApiKeyCreate, ApiKeyResponse

router = APIRouter(prefix="/api/keys", tags=["api_keys"])
logger = logging.getLogger(__name__)


async def get_user_repository():
    return UserRepository(db_pool=await get_db_pool())


@router.post("", response_model=ApiKeyResponse)
async def create_api_key(
        api_key_data: ApiKeyCreate,
        current_user: Dict[str, Any] = Depends(get_current_user),
        user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Create a new API key for the authenticated user.
    This endpoint is for creating API keys that can be used in CI environments.
    """
    user_id = current_user["sub"]

    # Generate a new API key with a prefix for identification
    key_prefix = "baid-"
    api_key = f"{key_prefix}{secrets.token_hex(24)}"

    # Store the API key in the database
    try:
        key_id = await user_repository.store_api_key(
            user_id=user_id,
            api_key=api_key,
            name=api_key_data.name,
            expires_at=(datetime.now() + timedelta(days=api_key_data.expiry_days)) if api_key_data.expiry_days else None
        )

        return {
            "key_id": key_id,
            "api_key": api_key,  # Only shown once at creation time
            "name": api_key_data.name,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(
                days=api_key_data.expiry_days)).isoformat() if api_key_data.expiry_days else None
        }
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
        current_user: Dict[str, Any] = Depends(get_current_user),
        user_repository: UserRepository = Depends(get_user_repository)
):
    """List all API keys for the authenticated user (without the actual key values)."""
    user_id = current_user["sub"]

    try:
        keys = await user_repository.get_user_api_keys(user_id)
        return keys
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.delete("/{key_id}")
async def delete_api_key(
        key_id: str,
        current_user: Dict[str, Any] = Depends(get_current_user),
        user_repository: UserRepository = Depends(get_user_repository)
):
    """Delete an API key."""
    user_id = current_user["sub"]

    try:
        await user_repository.delete_api_key(user_id, key_id)
        return {"message": "API key deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete API key")