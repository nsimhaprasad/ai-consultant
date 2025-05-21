import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, Any, Union, Optional

from fastapi import APIRouter, Depends, Header, HTTPException # Added HTTPException
from typing import Dict, Any # Added Dict, Any

# Removed direct db imports and local repository provider
# from baid_server.db.database import get_db_pool
# from baid_server.db.repositories.user_repository import UserRepository
from baid_server.services.auth_service import AuthService
from baid_server.services.dependencies import get_auth_service # Added

router = APIRouter(prefix="/api/auth", tags=["auth"]) # Prefix is fine, matches other auth routes
logger = logging.getLogger(__name__)


# Removed local get_user_repository function

@router.post("/api-key", response_model=Dict[str, Any]) # Added response_model
async def authenticate_with_api_key(
        api_key: str = Header(..., description="API Key for authentication"),
        auth_service: AuthService = Depends(get_auth_service) # Injected AuthService
):
    """
    Authenticate using an API key.
    Returns a session token that can be used for subsequent requests.
    This is primarily for CI environments where browser-based authentication is not possible.
    """
    try:
        # Logic moved to AuthService.authenticate_via_api_key
        # This service method will handle validation and token creation.
        # It will raise HTTPException on errors (e.g., invalid key).
        token_data = await auth_service.authenticate_via_api_key(api_key)
        return token_data

    except HTTPException: # Re-raise HTTPExceptions from the service
        raise
    except Exception as e:
        logger.error(f"API key authentication error: {str(e)}")
        # Generic error for unexpected issues
        raise HTTPException(status_code=500, detail="Authentication failed due to an internal server error.")