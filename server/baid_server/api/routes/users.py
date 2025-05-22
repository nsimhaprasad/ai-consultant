"""User management routes."""
import logging
import os
# import re # No longer needed here, moved to service
from typing import Dict, List, Any # List needed for generate_users_html type hint
# from datetime import datetime, timezone # No longer needed here, moved to service
from fastapi import APIRouter, Depends, Request, HTTPException # Added HTTPException for potential direct use
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field # Added for request models

# Removed direct repository and db_pool imports
# from baid_server.api.dependencies import get_current_user # Not used in these routes
# from baid_server.db.repositories.user_repository import UserRepository
# from baid_server.db.repositories.message_repository import MessageRepository
# from baid_server.db.database import get_db_pool
from baid_server.services.user_service import UserService # Added
from baid_server.services.dependencies import get_user_service # Added


logger = logging.getLogger(__name__)

# Helper functions estimate_tokens and format_relative_time moved to UserService or a utils module.
# For generate_users_html, it's kept here as it's purely presentation for this route.

# --- Request Models ---
class UserStatusUpdateRequest(BaseModel):
    user_id: str
    status: str = Field(..., pattern="^(active|restricted)$") # Add validation

class UserTokenLimitUpdateRequest(BaseModel):
    user_id: str
    token_limit: int = Field(..., ge=1000) # Add validation

class DefaultTokenLimitUpdateRequest(BaseModel):
    token_limit: int = Field(..., ge=1000) # Add validation


# Create router
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/status", response_model=Dict[str, Any]) # Specify response model
async def update_user_status_route( # Renamed to avoid conflict
    request_data: UserStatusUpdateRequest, # Use Pydantic model for request body
    user_service: UserService = Depends(get_user_service)
):
    """Update a user's status (active/restricted)."""
    # Logic moved to UserService.update_user_status_in_service
    # Service will raise HTTPException on errors.
    return await user_service.update_user_status_in_service(
        user_id=request_data.user_id, 
        new_status=request_data.status
    )


@router.post("/token-limit", response_model=Dict[str, Any])
async def update_token_limit_route( # Renamed
    request_data: UserTokenLimitUpdateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Update a user's token limit."""
    return await user_service.update_user_token_limit_in_service(
        user_id=request_data.user_id,
        token_limit=request_data.token_limit
    )


@router.post("/default-token-limit", response_model=Dict[str, Any])
async def update_default_token_limit_route( # Renamed
    request_data: DefaultTokenLimitUpdateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Update the default token limit for new users."""
    return await user_service.update_global_default_token_limit_in_service(
        token_limit=request_data.token_limit
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def get_users_dashboard_route(user_service: UserService = Depends(get_user_service)): #Renamed
    """Get a dashboard showing all users with message counts, token counts, and actions."""
    try:
        dashboard_data = await user_service.get_users_dashboard_data()
        # Generate HTML response using the data from the service
        html_content = generate_users_html(
            users=dashboard_data["users"], 
            default_token_limit=dashboard_data["default_token_limit"]
        )
        return HTMLResponse(content=html_content)
    
    except HTTPException: # Re-raise HTTPExceptions from service
        raise
    except Exception as e:
        logger.error(f"Error fetching users dashboard: {str(e)}")
        # Fallback HTML error, or could be a JSON response if preferred for API consistency
        return HTMLResponse(content=f"<h1>Error</h1><p>Could not load dashboard data.</p>", status_code=500)


def generate_users_html(users: List[Dict[str, Any]], default_token_limit: int = 100000) -> str:
    """Generate HTML for the users dashboard using Jinja2 template."""
    # Set up Jinja2 environment
    # Ensure templates_dir path is correct relative to this file's new location if it moves,
    # or use absolute paths / package resources.
    # Assuming this file stays in routes, path is server/templates/users/dashboard.html
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template('users/dashboard.html') # Path relative to templates_dir
    
    # Render the template with the provided data
    html = template.render(
        users=users,
        default_token_limit=default_token_limit
    )
    
    return html
