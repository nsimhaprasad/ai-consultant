"""Service layer for session management."""
import logging
from typing import List, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status

from baid_server.db.repositories.session_repository import SessionRepository
# Assuming SessionResponse model will be defined or imported if needed for transforming output
# For now, using Dict as per repository, but Pydantic models are better.

logger = logging.getLogger(__name__)


class SessionService:
    """Service for session-related operations."""

    def __init__(self, session_repo: SessionRepository):
        self._session_repo = session_repo

    async def get_sessions_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        try:
            sessions = await self._session_repo.get_user_sessions(user_id)
            # Here you could transform data into Pydantic response models if desired
            return sessions
        except Exception as e:
            logger.error(f"Error getting sessions for user {user_id} in service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve sessions.",
            )

    async def delete_user_session(self, user_id: str, session_id: str) -> None:
        """Delete a specific session for a user."""
        try:
            # Optionally, first check if session exists and belongs to user if repo doesn't handle this
            # session = await self._session_repo.get_session_by_id_and_user(session_id, user_id)
            # if not session:
            #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
            
            await self._session_repo.delete_session(user_id, session_id)
            # No return value needed for a successful deletion (204 No Content from route)
        except Exception as e:
            logger.error(f"Error deleting session {session_id} for user {user_id} in service: {str(e)}")
            # Consider specific exceptions, e.g., if the session doesn't exist (though delete is often idempotent)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete session {session_id}.",
            )
