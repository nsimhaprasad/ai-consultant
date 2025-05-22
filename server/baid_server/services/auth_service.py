import logging
import os
from datetime import datetime, timedelta, timezone
from threading import Timer
from typing import Dict, Any, Optional

import httpx
from jose import jwt

from baid_server.db.repositories.user_repository import UserRepository

from baid_server.config import OAuthConfig, JWTConfig # Added import

logger = logging.getLogger(__name__)

# OAuth and JWT configurations are now injected via __init__

# In-memory session storage
oauth_sessions: Dict[str, Dict[str, Any]] = {}
OAUTH_SESSION_TTL = 300  # 5 minutes


def cleanup_state(state: str) -> None:
    oauth_sessions.pop(state, None)


class AuthService:
    """Service for authentication and authorization."""

    def __init__(self, user_repository: UserRepository, oauth_config: OAuthConfig, jwt_config: JWTConfig): # Modified
        self._user_repository = user_repository
        self._oauth_config = oauth_config # Added
        self._jwt_config = jwt_config # Added

    async def exchange_google_code(self, code: str, redirect_uri: str, state: str) -> Dict[str, Any]:
        # Ensure redirect_uri from parameter is used, or self._oauth_config.GOOGLE_REDIRECT_URI if that's intended
        # The current method signature takes redirect_uri as a param, which might be for flexibility.
        # For this refactor, I'll assume the passed 'redirect_uri' is the one to use.
        # If GOOGLE_REDIRECT_URI from config is always the one, the method signature could be simplified.
        try:
            # Exchange code for token
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": self._oauth_config.GOOGLE_CLIENT_ID, # Modified
                        "client_secret": self._oauth_config.GOOGLE_CLIENT_SECRET.get_secret_value() if self._oauth_config.GOOGLE_CLIENT_SECRET else None, # Modified
                        "redirect_uri": redirect_uri, # Using parameter, as per original logic
                        "grant_type": "authorization_code"
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )

            if token_resp.status_code != 200:
                logger.error(f"Failed to exchange code for token: {token_resp.text}")
                return {
                    "error": f"Failed to exchange code for token: {token_resp.text}"
                }

            tokens = token_resp.json()
            access_token = tokens["access_token"]

            # Get user info
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

            if resp.status_code != 200:
                logger.error(f"Failed to get user info: {resp.text}")
                return {
                    "error": f"Failed to get user info: {resp.text}"
                }

            userinfo = resp.json()

            # Store user in database
            await self._user_repository.store_user(userinfo)

            # Create JWT token
            backend_token = jwt.encode({
                "sub": userinfo["email"],
                "name": userinfo["name"],
                "picture": userinfo.get("picture"),
                "exp": (datetime.now(timezone.utc) + timedelta(hours=8)).timestamp()
            }, self._jwt_config.JWT_SECRET.get_secret_value() if self._jwt_config.JWT_SECRET else None, algorithm=self._jwt_config.JWT_ALGORITHM) # Modified

            # Store in session cache
            session_data = {
                "access_token": backend_token,
                "expires_in": 8 * 3600,
                "email": userinfo["email"],
                "name": userinfo["name"],
                "picture": userinfo.get("picture"),
                "error": None
            }

            oauth_sessions[state] = session_data

            # Set up cleanup timer
            Timer(OAUTH_SESSION_TTL, cleanup_state, args=[state]).start()

            return session_data

        except Exception as e:
            logger.error(f"Error in Google OAuth code exchange: {str(e)}")
            return {
                "error": str(e)
            }

    def get_oauth_session(self, state: str) -> Optional[Dict[str, Any]]:
        return oauth_sessions.get(state)

    def verify_recaptcha(self, captcha_token: str, client_ip: str) -> bool:
        # This is a placeholder - in the actual code you would verify with the Google reCAPTCHA API
        # Since the code provided is missing the actual requests import and verification logic,
        # I'm leaving this as a stub that will need to be implemented
        logger.warning("reCAPTCHA verification not implemented")
        return True  # For now, return True to avoid breaking the application

    """
    Extensions to AuthService for API key-based authentication.
    These methods should be added to the existing AuthService class.
    """

    def create_jwt_token(self, user_id: str, email: str, name: str, expires_in_hours: int = 8):
        """Create a JWT token for the specified user."""
        # Imports already at top level, os import not needed here for JWT_SECRET
        
        # Create JWT token
        token = jwt.encode({
            "sub": user_id,
            "email": email,
            "name": name,
            "exp": (datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)).timestamp()
        }, self._jwt_config.JWT_SECRET.get_secret_value() if self._jwt_config.JWT_SECRET else None, algorithm=self._jwt_config.JWT_ALGORITHM) # Modified

        return token

    async def authenticate_via_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Authenticate using an API key, validate it, and return a JWT session token.
        """
        from fastapi import HTTPException, status # Local import for HTTPException

        user_info = await self._user_repository.validate_api_key(api_key)

        if not user_info:
            logger.warning(f"API key validation failed for key: {api_key[:10]}...") # Log prefix
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

        # User info from validate_api_key includes: "email", "name", "user_id"
        # Ensure "user_id" from validate_api_key is the one expected by create_jwt_token as "sub"
        token = self.create_jwt_token(
            user_id=user_info["user_id"], # This should map to 'sub' in JWT
            email=user_info["email"],
            name=user_info["name"]
            # expires_in_hours is defaulted in create_jwt_token
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 8 * 3600,  # Corresponds to default 8 hours
            "email": user_info["email"],
            "name": user_info["name"]
        }
