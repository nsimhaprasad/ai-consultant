from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    """Base model for tenant operations."""
    name: str = Field(..., description="The name of the tenant")
    slug: str = Field(..., description="URL-friendly identifier for the tenant")


class TenantCreate(TenantBase):
    """Model for creating a new tenant."""
    pass


class TenantResponse(TenantBase):
    """Response model for a tenant."""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
