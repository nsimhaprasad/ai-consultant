"""Sync models for baid-sync functionality."""
from pydantic import BaseModel


class SignedUrlRequest(BaseModel):
    """Request model for getting a signed URL for compressed archive upload."""
    filename: str
    content_type: str


class SignedUrlResponse(BaseModel):
    """Response model containing a signed URL for archive upload."""
    signed_url: str
    expires_at: str  # ISO timestamp when URL expires