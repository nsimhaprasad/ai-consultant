import logging
import os
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Depends

from baid_server.db.repositories.user_repository import UserRepository
from baid_server.models.waitlist import WaitlistRequest, WaitlistResponse
from baid_server.services.auth_service import AuthService

router = APIRouter(tags=["waitlist"])
logger = logging.getLogger(__name__)


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repository=user_repository)


@router.post("/api/waitlist", response_model=WaitlistResponse)
async def register_waitlist(
    request: Request, 
    waitlist_req: WaitlistRequest,
    user_repository: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    request_id = os.urandom(4).hex()
    logger.info(f"[{request_id}] Waitlist registration request received for: {waitlist_req.email}")

    # Get the client's IP address
    client_ip = request.client.host
    logger.info(f"[{request_id}] Client IP: {client_ip}")

    # Verify reCAPTCHA token
    if not waitlist_req.captcha:
        logger.warning(f"[{request_id}] Missing captcha token for: {waitlist_req.email}")
        raise HTTPException(status_code=400, detail="Captcha verification failed")

    # Verify with reCAPTCHA service
    recaptcha_verified = auth_service.verify_recaptcha(
        captcha_token=waitlist_req.captcha,
        client_ip=client_ip
    )
    
    if not recaptcha_verified:
        logger.warning(f"[{request_id}] reCAPTCHA verification failed for: {waitlist_req.email}")
        raise HTTPException(status_code=400, detail="Captcha verification failed")

    try:
        # Store user in the waitlist
        await user_repository.add_to_waitlist(
            email=str(waitlist_req.email),
            name=waitlist_req.name,
            role=waitlist_req.role,
            referral_source=waitlist_req.referral_source,
            ip_address=client_ip
        )

        logger.info(f"[{request_id}] User added to waitlist: {waitlist_req.email} (IP: {client_ip})")

        return {
            "status": "success",
            "message": "Thank you for joining our waitlist!",
            "email": waitlist_req.email
        }

    except Exception as e:
        logger.error(f"[{request_id}] Error adding user to waitlist: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register: {str(e)}")
