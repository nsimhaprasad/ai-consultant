from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr

class ApiKeyBase(BaseModel):
    """Base model for API key operations."""
    name: str = Field(..., description="A friendly name for the API key")
    tenant_id: Optional[UUID] = Field(None, description="ID of the tenant this API key belongs to")


class ApiKeyCreate(ApiKeyBase):
    """Model for creating a new API key."""
    expiry_days: Optional[int] = Field(None, description="Number of days until the key expires. None means no expiration.")


class ApiKeyResponse(ApiKeyBase):
    """Response model for an API key."""
    key_id: str
    api_key: Optional[str] = Field(None, description="The actual API key, only shown on creation")
    created_at: str
    expires_at: Optional[str] = None