"""Service layer for message management."""
import logging
from typing import List, Dict, Any

from fastapi import HTTPException, status

from baid_server.db.repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)


class MessageService:
    """Service for message-related operations."""

    def __init__(self, message_repo: MessageRepository):
        self._message_repo = message_repo

    async def get_session_history_for_user(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        """Get session history for a user."""
        try:
            history = await self._message_repo.get_session_history(user_id, session_id)
            if not history: # Check if history is empty and raise 404 as per original route logic
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No history found for session {session_id}"
                )
            return history
        except HTTPException: # Re-raise HTTPException if it's already one (like the 404 above)
            raise
        except Exception as e:
            logger.error(f"Error getting session history for user {user_id}, session {session_id} in service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve session history.",
            )
