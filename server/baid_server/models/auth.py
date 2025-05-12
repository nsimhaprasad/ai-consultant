from typing import Optional

from pydantic import BaseModel


class GoogleCodeRequest(BaseModel):
    """Request model for Google OAuth code exchange."""
    code: str
    redirect_uri: str


class GoogleTokenRequest(BaseModel):
    """Request model for Google token validation."""
    google_token: str


class TokenPayload(BaseModel):
    """Model for JWT token payload."""
    sub: str  # User email
    name: str
    picture: Optional[str] = None
    exp: float  # Expiration timestamp
