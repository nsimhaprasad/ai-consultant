import logging
import os
from typing import Any, Union

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from starlette.responses import JSONResponse

# Removed direct imports of UserRepository, OAuthConfig, JWTConfig, and their providers,
# as get_auth_service is now imported from services.dependencies
from baid_server.services.auth_service import AuthService
from baid_server.services.dependencies import get_auth_service # MODIFIED: Import centralized provider

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


# Removed local definition of get_auth_service. It's now imported.

@router.get("/google-login")
async def google_login_redirect(
        request: Request,
        auth_service: AuthService = Depends(get_auth_service)
):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    if not code or not state:
        html_content = """
        <html><body><h2>Login failed!</h2><p>Missing code or state.</p></body></html>
        """
        return HTMLResponse(content=html_content, status_code=400)

    # Process the Google OAuth code
    result = await auth_service.exchange_google_code(code, redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", ""), state=state)

    if "error" in result and result["error"]:
        html_content = f"""
        <html><body><h2>Login failed!</h2><p>{result["error"]}</p></body></html>
        """
        return HTMLResponse(content=html_content, status_code=400)

    # Success response
    html_content = """
    <html><head><title>Login Successful</title></head>
    <body style='font-family:sans-serif;text-align:center;margin-top:10em;'>
        <h2>Login successful!</h2>
        <p>You may now return to your IDE to enjoy BAID agent.</p>
        <p>You can close this window.</p>
    </body></html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@router.get("/session", response_model=None)
async def get_oauth_session(
        state: str,
        auth_service: AuthService = Depends(get_auth_service)
) -> Union[JSONResponse, dict[str, Any]]:
    session = auth_service.get_oauth_session(state)
    if not session:
        return JSONResponse(
            status_code=404,
            content={"error": "Session not found or expired"}
        )
    return JSONResponse(content=session)
