import logging
import os
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID

import asyncpg # Added import
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from fastapi.responses import JSONResponse

from baid_server.api.dependencies import get_current_user
from baid_server.db.database import get_db_pool
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.models.api_key import ApiKeyCreate, ApiKeyResponse
from baid_server.services.api_key_service import ApiKeyService
from baid_server.services.dependencies import get_api_key_service

router = APIRouter(prefix="/api/keys", tags=["api_keys"])
logger = logging.getLogger(__name__)


# Removed local get_user_repository function
# This is now handled by centralized dependencies in db.dependencies.py
# and consumed by service dependencies in services.dependencies.py

@router.post("", response_model=dict)
async def create_api_key(
        api_key_data: ApiKeyCreate,
        current_user: Dict[str, Any] = Depends(get_current_user),
        service: ApiKeyService = Depends(get_api_key_service), # Modified
):
    """Create a new API key for the authenticated user."""
    user_id = current_user["sub"]
    # Logic moved to ApiKeyService
    return await service.create_api_key(api_key_data=api_key_data, user_id=user_id)


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
        current_user: Dict[str, Any] = Depends(get_current_user),
        service: ApiKeyService = Depends(get_api_key_service), # Modified
        tenant_id: Optional[UUID] = Query(None, description="Filter keys by tenant ID")
):
    """List all API keys for the authenticated user."""
    user_id = current_user["sub"]
    # Logic moved to ApiKeyService
    return await service.list_api_keys(user_id=user_id, tenant_id=tenant_id)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
        key_id: str = Path(..., description="ID of the API key to delete"),
        current_user: Dict[str, Any] = Depends(get_current_user),
        service: ApiKeyService = Depends(get_api_key_service), # Modified
        tenant_id: Optional[UUID] = Query(None, description="Tenant ID for the key")
):
    """Delete an API key."""
    user_id = current_user["sub"]
    # Logic moved to ApiKeyService
    await service.delete_api_key(user_id=user_id, key_id=key_id, tenant_id=tenant_id)
    # For HTTP 204, FastAPI expects no response body.
    # If service.delete_api_key raises an exception, FastAPI handles it.
    # If it completes successfully, FastAPI sends a 204 response.
    return 