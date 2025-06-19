"""Sync routes for baid-sync functionality."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from baid_server.api.dependencies import get_current_user
from baid_server.models.sync import SignedUrlRequest, SignedUrlResponse
from baid_server.services.sync_service import SyncService

router = APIRouter(prefix="/api/sync", tags=["sync"])
logger = logging.getLogger(__name__)


def get_sync_service() -> SyncService:
    """Dependency to get sync service instance."""
    return SyncService()


@router.post("/signed-url", response_model=SignedUrlResponse)
async def get_signed_url(
    request: SignedUrlRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    sync_service: SyncService = Depends(get_sync_service)
):
    """Get signed URL for uploading compressed archive to Google Cloud Storage.
    
    This endpoint generates a signed URL that allows baid-sync clients to upload
    compressed directory archives directly to Google Cloud Storage without exposing credentials.
    
    Args:
        request: Request containing filename and content type
        current_user: Authenticated user from JWT token
        sync_service: Service for handling sync operations
        
    Returns:
        Response containing signed URL and expiration time
        
    Raises:
        HTTPException: If validation fails or service error occurs
    """
    try:
        # Extract user ID from token
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        # Validate request
        sync_service.validate_sync_request(
            request.filename, 
            request.content_type
        )

        # Generate signed URL
        signed_url = sync_service.generate_signed_url(
            filename=request.filename,
            content_type=request.content_type,
            user_id=user_id
        )

        # Calculate expiration time
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat() + "Z"

        logger.info(f"Generated signed URL for user {user_id}, file {request.filename}")

        return SignedUrlResponse(
            signed_url=signed_url,
            expires_at=expires_at
        )

    except ValueError as e:
        logger.warning(f"Validation error in signed URL request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating signed URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_sync_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    sync_service: SyncService = Depends(get_sync_service)
):
    """Get sync service status and configuration.
    
    This endpoint provides information about the sync service status
    and storage configuration for debugging and monitoring.
    
    Args:
        current_user: Authenticated user from JWT token
        sync_service: Service for handling sync operations
        
    Returns:
        Status information about the sync service
    """
    try:
        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        bucket_info = sync_service.get_bucket_info()
        
        status = {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "user_id": user_id,
            "storage": bucket_info,
            "url_expiration_hours": sync_service.url_expiration_hours
        }

        logger.info(f"Sync status requested by user {user_id}")
        return JSONResponse(content=status)

    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")