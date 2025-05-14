import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Dict, Any, Union, Optional

from baid_server.db.database import get_db_pool
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


# Add this to the existing auth.py file


async def get_user_repository():
    return UserRepository(db_pool=await get_db_pool())


@router.post("/api-key")
async def authenticate_with_api_key(
        api_key: str = Header(..., description="API Key for authentication"),
        user_repository: UserRepository = Depends(get_user_repository)
):
    """
    Authenticate using an API key.
    Returns a session token that can be used for subsequent requests.
    This is primarily for CI environments where browser-based authentication is not possible.
    """
    try:
        # Validate API key and get user info
        print("api key")
        print(api_key)
        user_info = await user_repository.validate_api_key(api_key)

        if not user_info:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Create a JWT token for the authenticated user
        auth_service = AuthService(user_repository=user_repository)
        token = auth_service.create_jwt_token(
            user_id=user_info["user_id"],
            email=user_info["email"],
            name=user_info["name"]
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 28800,  # 8 hours in seconds
            "email": user_info["email"],
            "name": user_info["name"]
        }

    except Exception as e:
        logger.error(f"API key authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")