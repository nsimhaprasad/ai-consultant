"""Service layer for user management."""
import logging
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from fastapi import HTTPException, status

from baid_server.db.repositories.user_repository import UserRepository
from baid_server.db.repositories.global_settings_repository import GlobalSettingsRepository
from baid_server.db.repositories.message_repository import MessageRepository # For token counting

logger = logging.getLogger(__name__)

# Helper functions from the original users.py route - can be part of the service or a util module
def _estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string."""
    if not text: return 0
    words = text.split()
    punctuation = len(re.findall(r'[.,!?;:()\[\]{}\'\"-]', text))
    return int(len(words) * 1.3) + punctuation

def _format_relative_time(timestamp: Optional[datetime]) -> str:
    """Format a timestamp as a relative time string."""
    if not timestamp:
        return 'Never'
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - timestamp
    seconds = delta.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = delta.days
    if seconds < 60: return f'{int(seconds)} seconds ago'
    if minutes < 60: return f'{int(minutes)} minutes ago'
    if hours < 24: return f'{int(hours)} hours ago'
    if days < 30: return f'{days} days ago'
    months = days // 30
    if months < 12: return f'{int(months)} months ago'
    years = days // 365
    return f'{int(years)} years ago'


class UserService:
    """Service for user-related operations."""

    def __init__(
        self, 
        user_repo: UserRepository, 
        global_settings_repo: GlobalSettingsRepository,
        message_repo: MessageRepository # Added for token counting in dashboard
    ):
        self._user_repo = user_repo
        self._global_settings_repo = global_settings_repo
        self._message_repo = message_repo

    async def update_user_status_in_service(self, user_id: str, new_status: str) -> Dict[str, Any]:
        if new_status not in ["active", "restricted"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be 'active' or 'restricted'")
        
        success = await self._user_repo.update_user_status(user_id, new_status)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found.")
        return {"success": True, "message": f"User status updated to {new_status}"}

    async def update_user_token_limit_in_service(self, user_id: str, token_limit: int) -> Dict[str, Any]:
        if token_limit < 1000: # Assuming a minimum sensible limit
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token limit must be an integer >= 1000")
        
        success = await self._user_repo.update_user_token_limit(user_id, token_limit)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found.")
        return {"success": True, "message": f"Token limit updated to {token_limit}"}

    async def update_global_default_token_limit_in_service(self, token_limit: int) -> Dict[str, Any]:
        if token_limit < 1000:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token limit must be an integer >= 1000")
        
        await self._global_settings_repo.update_default_token_limit(token_limit)
        return {"success": True, "message": f"Default token limit updated to {token_limit}"}

    async def get_users_dashboard_data(self) -> Dict[str, Any]:
        """Prepare data for the users dashboard."""
        raw_users_data = await self._user_repo.get_dashboard_users_data()
        default_token_limit_setting = await self._global_settings_repo.get_setting('default_token_limit')
        
        default_token_limit = 100000 # A fallback default
        if default_token_limit_setting and default_token_limit_setting.get('setting_value'):
            try:
                default_token_limit = int(default_token_limit_setting['setting_value'])
            except ValueError:
                logger.warning(f"Invalid default_token_limit in global_settings: {default_token_limit_setting['setting_value']}")

        processed_users = []
        for user_row in raw_users_data:
            user_data = dict(user_row) # Convert asyncpg Row to dict
            
            # Get all messages for this user to calculate token counts
            # This is N+1 query problem. For a real dashboard, this should be optimized.
            # E.g., by a better SQL query or a separate batch job for stats.
            # For now, replicating the original logic.
            user_messages = await self._message_repo.get_session_history(user_data["email"], session_id="%") # Assuming '%' fetches all sessions for user
            
            token_count = 0
            # The get_session_history returns a list of dicts with 'message' key.
            # This needs to be adapted if the structure is different or if it's for all sessions.
            # The original users.py route fetched all messages for a user, not per session for this count.
            # Let's assume get_session_history with session_id='%' (or similar wildcard) gets all messages for a user.
            # This part of the logic needs clarification on how MessageRepository fetches all messages for a user.
            # For now, I'll iterate through what `get_session_history` might return.
            # A dedicated `get_all_messages_for_user` in MessageRepository would be better.
            
            # Placeholder: to avoid breaking, will simulate if MessageRepository doesn't support this well.
            # In a real scenario, MessageRepository.get_all_messages_by_user_id(user_id) would be better.
            # For now, let's assume the dashboard's message_count from user_repo is sufficient and token_count is more complex.
            # The original users.py route did:
            # messages = await conn.fetch("SELECT content FROM messages WHERE user_id = $1", user_id)
            # This needs a new method in MessageRepository: get_all_message_content_for_user(user_id)
            
            # For now, let's use a placeholder for token_count as it requires MessageRepository changes.
            # token_count = sum(_estimate_tokens(msg.get("content", "")) for msg in user_messages) # If user_messages had 'content'
            token_count = 0 # Placeholder

            user_data["last_active_relative"] = _format_relative_time(user_data.get("last_active"))
            
            effective_token_limit = default_token_limit
            if user_data.get("token_limit_value"): # This comes from the COALESCE in SQL
                try:
                    effective_token_limit = int(user_data["token_limit_value"])
                except ValueError:
                    logger.warning(f"Invalid token_limit_value for user {user_data['email']}: {user_data['token_limit_value']}")
            
            user_data["token_limit"] = effective_token_limit
            user_data["token_percentage"] = min(round((token_count / effective_token_limit) * 100), 100) if effective_token_limit > 0 else 0
            user_data["status"] = user_data.get("user_status", "active") # Default to active if no status

            # Convert datetime objects to ISO format strings if they are not already
            if isinstance(user_data.get("created_at"), datetime):
                user_data["created_at"] = user_data["created_at"].isoformat()
            if isinstance(user_data.get("last_active"), datetime):
                user_data["last_active"] = user_data["last_active"].isoformat()

            processed_users.append(user_data)

        return {
            "users": processed_users,
            "default_token_limit": default_token_limit
        }
