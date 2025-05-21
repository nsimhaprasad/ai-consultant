import logging
import os
from typing import Dict, Any

from fastapi import APIRouter, Request, Depends # Removed HTTPException as service handles it

# Removed UserRepository and AuthService direct imports, and local providers
# from baid_server.db.repositories.user_repository import UserRepository
from baid_server.models.waitlist import WaitlistRequest, WaitlistResponse
# from baid_server.services.auth_service import AuthService
from baid_server.services.waitlist_service import WaitlistService # Added
from baid_server.services.dependencies import get_waitlist_service # Added

router = APIRouter(tags=["waitlist"])
logger = logging.getLogger(__name__)


# Removed local get_user_repository and get_auth_service functions

@router.post("/api/waitlist", response_model=WaitlistResponse)
async def register_waitlist(
    fastapi_request: Request, # Renamed to avoid conflict with WaitlistRequest model
    waitlist_req: WaitlistRequest,
    waitlist_service: WaitlistService = Depends(get_waitlist_service) # Injected WaitlistService
) -> Dict[str, Any]: # Return type matches WaitlistResponse structure
    request_id = os.urandom(4).hex() # Keep request_id for logging if desired
    logger.info(f"[{request_id}] Waitlist registration request received for: {waitlist_req.email}")

    client_ip = fastapi_request.client.host
    logger.info(f"[{request_id}] Client IP: {client_ip}")
    
    # Logic moved to WaitlistService.add_user_to_waitlist
    # The service method will handle reCAPTCHA verification and database interaction.
    # It will also raise appropriate HTTPErrors.
    response = await waitlist_service.add_user_to_waitlist(
        waitlist_req=waitlist_req,
        client_ip=client_ip
    )
    return response
