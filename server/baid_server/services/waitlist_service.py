"""Service layer for waitlist management."""
import logging
from typing import Optional, Dict, Any

from fastapi import HTTPException, status, Request

from baid_server.db.repositories.waitlist_repository import WaitlistRepository
from baid_server.services.auth_service import AuthService # For reCAPTCHA
from baid_server.models.waitlist import WaitlistRequest, WaitlistResponse # Assuming this exists

logger = logging.getLogger(__name__)


class WaitlistService:
    """Service for waitlist-related operations."""

    def __init__(self, waitlist_repo: WaitlistRepository, auth_service: AuthService):
        self._waitlist_repo = waitlist_repo
        self._auth_service = auth_service

    async def add_user_to_waitlist(
        self,
        waitlist_req: WaitlistRequest,
        client_ip: str # Changed from full Request to just client_ip for service layer
    ) -> Dict[str, Any]: # Based on current route response
        """
        Add a user to the waitlist after verifying reCAPTCHA.
        """
        # Verify reCAPTCHA token
        if not waitlist_req.captcha:
            logger.warning(f"Missing captcha token for: {waitlist_req.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captcha verification failed: Missing token.")

        recaptcha_verified = self._auth_service.verify_recaptcha(
            captcha_token=waitlist_req.captcha,
            client_ip=client_ip
        )
        
        if not recaptcha_verified:
            logger.warning(f"reCAPTCHA verification failed for: {waitlist_req.email}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Captcha verification failed: Invalid token.")

        try:
            await self._waitlist_repo.add_to_waitlist(
                email=str(waitlist_req.email), # Ensure Pydantic EmailStr is converted if needed
                name=waitlist_req.name,
                role=waitlist_req.role,
                referral_source=waitlist_req.referral_source,
                ip_address=client_ip
            )
            logger.info(f"User added to waitlist: {waitlist_req.email} (IP: {client_ip})")
            return { # Conforms to WaitlistResponse implicitly by dict structure
                "status": "success",
                "message": "Thank you for joining our waitlist!",
                "email": str(waitlist_req.email)
            }
        except Exception as e:
            logger.error(f"Error adding user {waitlist_req.email} to waitlist in service: {str(e)}")
            # Avoid exposing raw error messages if they could be sensitive
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register for the waitlist due to an internal error.",
            )
