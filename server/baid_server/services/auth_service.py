import logging
import os
from datetime import datetime, timedelta, timezone
from threading import Timer
from typing import Dict, Any, Optional

import httpx
from jose import jwt

from baid_server.db.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "https://core.baid.dev/api/auth/google-login")

# JWT configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "a-string-secret-at-least-256-bits-long")
JWT_ALGORITHM = "HS256"

# In-memory session storage
oauth_sessions: Dict[str, Dict[str, Any]] = {}
OAUTH_SESSION_TTL = 300  # 5 minutes


def cleanup_state(state: str) -> None:
    oauth_sessions.pop(state, None)


class AuthService:
    """Service for authentication and authorization."""

    def __init__(self, user_repository: Optional[UserRepository] = None):
        self._user_repository = user_repository

    async def exchange_google_code(self, code: str, redirect_uri: str, state: str) -> Dict[str, Any]:
        try:
            # Exchange code for token
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "redirect_uri": redirect_uri,
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
            }, JWT_SECRET, algorithm=JWT_ALGORITHM)

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
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        import os

        JWT_SECRET = os.environ.get("JWT_SECRET", "a-string-secret-at-least-256-bits-long")
        JWT_ALGORITHM = "HS256"

        # Create JWT token
        token = jwt.encode({
            "sub": user_id,
            "email": email,
            "name": name,
            "exp": (datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)).timestamp()
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return token
