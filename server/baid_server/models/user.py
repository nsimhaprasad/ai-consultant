from typing import Optional, List, Dict, Any

from pydantic import BaseModel


class UserInfo(BaseModel):
    """Model for user information."""
    email: str
    name: str
    picture: Optional[str] = None


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str
    user_id: str
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None


class MessageInfo(BaseModel):
    """Model for message information."""
    role: str
    message: str
    timestamp: Optional[str] = None


class UserSessionsResponse(BaseModel):
    """Response model for user sessions API."""
    user_id: str
    sessions: List[SessionInfo]


class SessionHistoryResponse(BaseModel):
    """Response model for session history API."""
    user_id: str
    session_id: str
    history: List[MessageInfo]


class ConsultRequest(BaseModel):
    """Request model for consultation API."""
    prompt: str
    context: Dict[str, Any] = {}
