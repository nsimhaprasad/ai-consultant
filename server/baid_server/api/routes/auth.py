import logging
import os
from typing import Any, Union

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from starlette.responses import JSONResponse

from baid_server.db.database import get_db_pool
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


async def get_user_repository() -> UserRepository:
    return UserRepository(
        db_pool= await get_db_pool()
    )


def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repository=user_repository)


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
