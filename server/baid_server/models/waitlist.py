from typing import Optional

from pydantic import BaseModel, EmailStr


class WaitlistRequest(BaseModel):
    """Request model for waitlist registration."""
    email: EmailStr
    name: Optional[str] = None
    role: Optional[str] = None
    referral_source: Optional[str] = None
    captcha: str


class WaitlistResponse(BaseModel):
    """Response model for waitlist registration."""
    status: str
    message: str
    email: EmailStr
