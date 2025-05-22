import logging
import os
from typing import Dict, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt

from baid_server.config import settings

# JWT configuration
JWT_SECRET = settings.JWT_SECRET.get_secret_value()
JWT_ALGORITHM = "HS256"

logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer()


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception as e:
        logger.error(f"JWT decode failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
