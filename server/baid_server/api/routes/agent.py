import logging
import os
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, Header, HTTPException, Depends
from fastapi.responses import StreamingResponse

from baid_server.api.dependencies import get_current_user
from baid_server.services.service_factory import ServiceFactory

router = APIRouter(tags=["agent"])
logger = logging.getLogger(__name__)

@router.post("/consult")
async def consult(
        request: Request,
        current_user: Dict[str, Any] = Depends(get_current_user),
        session_id: Optional[str] = Header(None, alias="session_id")
):
    request_id = os.urandom(4).hex()
    logger.info(f"[{request_id}] === Starting /consult request ===")
    
    user_id = current_user["sub"]

    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"[{request_id}] Failed to parse request body: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid request body")

    user_input = data.get("prompt", "")
    context = data.get("context", {})
    
    # Return streaming response
    return StreamingResponse(
        ServiceFactory.get_agent_service().process_query(
            user_id=user_id,
            session_id=session_id,
            user_input=user_input,
            context=context
        ),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        }
    )
