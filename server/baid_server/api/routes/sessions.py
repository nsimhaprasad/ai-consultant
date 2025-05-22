"""Session management routes."""
import logging
from typing import Dict, Any, List # Added List

from fastapi import APIRouter, HTTPException, Depends, status # Added status

from baid_server.api.dependencies import get_current_user
# Removed direct db imports and ServiceFactory
# from baid_server.db.database import get_db_pool
# from baid_server.db.repositories.message_repository import MessageRepository
# from baid_server.db.repositories.session_repository import SessionRepository
# from baid_server.services.service_factory import ServiceFactory
from baid_server.services.session_service import SessionService # Added
from baid_server.services.message_service import MessageService # Added
from baid_server.services.agent_service import AgentService # Added
from baid_server.services.dependencies import ( # Added
    get_session_service,
    get_message_service,
    get_agent_service,
)
# Assuming a SessionResponse model might be good for standardizing output
# from baid_server.models.session import SessionResponse # Example if you create such a model

router = APIRouter(tags=["sessions"])
logger = logging.getLogger(__name__)


# Removed local repository providers: get_session_repository, get_message_repository

@router.get("/sessions/{user_id}") # Consider response_model=List[SessionResponse]
async def get_user_sessions(
    user_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user), 
    session_service: SessionService = Depends(get_session_service) # Injected SessionService
):
    # Verify the user is requesting their own sessions or is an admin
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these sessions")
    
    sessions = await session_service.get_sessions_for_user(user_id)
    
    # Service layer can handle the 404 if no sessions are found, or controller can.
    # Keeping it here for now as per original logic.
    if not sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No sessions found for user {user_id}")

    return {"user_id": user_id, "sessions": sessions}


@router.get("/history/{user_id}/{session_id}") # Consider response_model for history
async def get_session_history(
    user_id: str, 
    session_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user),
    message_service: MessageService = Depends(get_message_service) # Injected MessageService
):
    # Verify the user is requesting their own history or is an admin
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this history")
    
    # The MessageService.get_session_history_for_user handles the 404 if history is not found.
    history = await message_service.get_session_history_for_user(user_id, session_id)
    
    return {
        "user_id": user_id,
        "session_id": session_id,
        "history": history
    }


@router.delete("/sessions/{user_id}/{session_id}", status_code=status.HTTP_204_NO_CONTENT) # Added 204
async def delete_session(
    user_id: str, 
    session_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user),
    session_service: SessionService = Depends(get_session_service), # Injected SessionService
    agent_service: AgentService = Depends(get_agent_service) # Injected AgentService
):
    # Verify the user is deleting their own session or is an admin
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this session")
    
    try:
        # Delete from ADK (Vertex AI Agent session) via AgentService
        # Note: AgentService.delete_session is not async, should be if it involves I/O
        # For now, assuming it's okay or will be fixed in AgentService if it's blocking.
        agent_service.delete_session(user_id, session_id) 
        
        # Delete from database via SessionService
        await session_service.delete_user_session(user_id, session_id)
        
        # For 204 No Content, no response body should be sent.
        # FastAPI handles this automatically if the function returns None.
        return
    
    except HTTPException: # Re-raise known HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id} for user {user_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error deleting session.")
