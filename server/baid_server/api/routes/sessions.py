"""Session management routes."""
import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends

from baid_server.api.dependencies import get_current_user
from baid_server.db.repositories.message_repository import MessageRepository
from baid_server.db.repositories.session_repository import SessionRepository
from baid_server.services.service_factory import ServiceFactory

router = APIRouter(tags=["sessions"])
logger = logging.getLogger(__name__)


@router.get("/sessions/{user_id}")
async def get_user_sessions(user_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    # Verify the user is requesting their own sessions or is an admin
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these sessions")
    
    sessions = await SessionRepository.get_user_sessions(user_id)
    
    if not sessions:
        raise HTTPException(status_code=404, detail=f"No sessions found for user {user_id}")

    return {"user_id": user_id, "sessions": sessions}


@router.get("/history/{user_id}/{session_id}")
async def get_session_history(
    user_id: str, 
    session_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # Verify the user is requesting their own history or is an admin
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this history")
    
    history = await MessageRepository.get_session_history(user_id, session_id)
    
    if not history:
        raise HTTPException(status_code=404, detail=f"No history found for session {session_id}")

    return {
        "user_id": user_id,
        "session_id": session_id,
        "history": history
    }


@router.delete("/sessions/{user_id}/{session_id}")
async def delete_session(
    user_id: str, 
    session_id: str, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # Verify the user is deleting their own session or is an admin
    if current_user["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this session")
    
    try:
        # Delete from ADK
        ServiceFactory.get_agent_service().delete_session(user_id, session_id)
        
        # Delete from database
        await SessionRepository.delete_session(user_id, session_id)
        
        return {"message": f"Session {session_id} for user {user_id} deleted successfully"}
    
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")
