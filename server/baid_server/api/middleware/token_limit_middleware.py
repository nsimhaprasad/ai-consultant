"""Token limit middleware to enforce user token limits."""
import logging
from typing import Optional, Dict, Any, Callable

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from baid_server.db.database import get_db_pool
from baid_server.api.routes.users import estimate_tokens

logger = logging.getLogger(__name__)


class TokenLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce token limits on API requests."""

    async def dispatch(self, request: Request, call_next: Callable):
        # Only check token limits for the /consult endpoint
        if request.url.path.endswith("/consult"):
            # Get user from request state (set by auth middleware)
            user = request.state.user if hasattr(request.state, "user") else None
            
            if user:
                user_id = user.get("sub")
                
                # Check if user is restricted
                is_restricted, token_usage, token_limit = await self._check_user_limits(user_id)
                
                if is_restricted:
                    logger.warning(f"User {user_id} is restricted from making requests")
                    raise HTTPException(
                        status_code=403,
                        detail="Your account is currently restricted. Please contact support."
                    )
                
                # Check token limits
                if token_usage >= token_limit:
                    logger.warning(f"User {user_id} has exceeded their token limit: {token_usage}/{token_limit}")
                    raise HTTPException(
                        status_code=429,
                        detail=f"You have reached your token limit ({token_usage}/{token_limit}). "
                               f"Please contact support to increase your limit."
                    )
                
                # Add token info to request state for logging
                request.state.token_info = {
                    "usage": token_usage,
                    "limit": token_limit
                }
                
                logger.info(f"User {user_id} token usage: {token_usage}/{token_limit}")
        
        # Continue processing the request
        response = await call_next(request)
        return response
    
    async def _check_user_limits(self, user_id: str) -> tuple[bool, int, int]:
        """Check if user is restricted and get their token usage and limits.
        
        Returns:
            Tuple of (is_restricted, token_usage, token_limit)
        """
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Check user status
            status_row = await conn.fetchrow(
                "SELECT status FROM user_status WHERE user_id = $1",
                user_id
            )
            
            is_restricted = False
            if status_row:
                is_restricted = status_row["status"].lower() == "restricted"
            
            # Get user-specific token limit if it exists
            user_limit_row = await conn.fetchrow(
                "SELECT setting_value FROM user_settings WHERE user_id = $1 AND setting_key = 'token_limit'",
                user_id
            )
            
            # Get default token limit from global settings
            default_limit_row = await conn.fetchrow(
                "SELECT setting_value FROM global_settings WHERE setting_key = 'default_token_limit'"
            )
            
            # Calculate token limit (user-specific or default)
            token_limit = int(user_limit_row["setting_value"]) if user_limit_row else \
                         int(default_limit_row["setting_value"]) if default_limit_row else 100000
            
            # Calculate current token usage
            messages = await conn.fetch(
                "SELECT content FROM messages WHERE user_id = $1",
                user_id
            )
            
            token_usage = 0
            for msg in messages:
                token_usage += estimate_tokens(msg["content"])
            
            return is_restricted, token_usage, token_limit
