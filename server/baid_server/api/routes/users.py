"""User management routes."""
import logging
import os
import re
from typing import Dict, List, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader

from baid_server.api.dependencies import get_current_user
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.db.repositories.message_repository import MessageRepository
from baid_server.db.database import get_db_pool


logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in a text string.
    
    This is a simple approximation based on common tokenization patterns.
    For more accurate counts, you would use a tokenizer like tiktoken or GPT-2 tokenizer.
    """
    # Split by whitespace for words
    words = text.split()
    # Count punctuation and special characters
    punctuation = len(re.findall(r'[.,!?;:()\[\]{}\'\"-]', text))
    # Estimate: roughly 1.3 tokens per word for English text
    return int(len(words) * 1.3) + punctuation


def format_relative_time(timestamp: datetime) -> str:
    """Format a timestamp as a relative time string (e.g., '5 minutes ago')."""
    if not timestamp:
        return 'Never'
        
    # Ensure timestamp is timezone-aware
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
        
    now = datetime.now(timezone.utc)
    delta = now - timestamp
    
    # Calculate the time difference
    seconds = delta.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = delta.days
    
    if seconds < 60:
        return f'{int(seconds)} seconds ago'
    elif minutes < 60:
        return f'{int(minutes)} minutes ago'
    elif hours < 24:
        return f'{int(hours)} hours ago'
    elif days < 30:
        return f'{days} days ago'
    elif days < 365:
        months = days // 30
        return f'{int(months)} months ago'
    else:
        years = days // 365
        return f'{int(years)} years ago'


# Create router
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/status")
async def update_user_status(request: Request):
    """Update a user's status (active/restricted)."""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        status = data.get("status")
        
        if not user_id or not status:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing user_id or status in request"}
            )
        
        if status not in ["active", "restricted"]:
            return JSONResponse(
                status_code=400,
                content={"error": "Status must be 'active' or 'restricted'"}
            )
        
        # Update user status in database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check if user exists
            user_exists = await conn.fetchval(
                "SELECT 1 FROM users WHERE email = $1", user_id
            )
            
            if not user_exists:
                return JSONResponse(
                    status_code=404,
                    content={"error": f"User {user_id} not found"}
                )
            
            # Insert or update user status
            await conn.execute(
                """
                INSERT INTO user_status (user_id, status, updated_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    status = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, status
            )
        
        logger.info(f"Updated status for user {user_id} to {status}")
        return {"success": True, "message": f"User status updated to {status}"}
    
    except Exception as e:
        logger.error(f"Error updating user status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


@router.post("/token-limit")
async def update_token_limit(request: Request):
    """Update a user's token limit."""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        token_limit = data.get("token_limit")
        
        if not user_id or not token_limit:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing user_id or token_limit in request"}
            )
        
        if not isinstance(token_limit, int) or token_limit < 1000:
            return JSONResponse(
                status_code=400,
                content={"error": "Token limit must be an integer >= 1000"}
            )
        
        # Update token limit in database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Check if user exists
            user_exists = await conn.fetchval(
                "SELECT 1 FROM users WHERE email = $1", user_id
            )
            
            if not user_exists:
                return JSONResponse(
                    status_code=404,
                    content={"error": f"User {user_id} not found"}
                )
            
            # Insert or update user token limit
            await conn.execute(
                """
                INSERT INTO user_settings (user_id, setting_key, setting_value, updated_at)
                VALUES ($1, 'token_limit', $2, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, setting_key) DO UPDATE SET
                    setting_value = $2,
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, str(token_limit)
            )
        
        logger.info(f"Updated token limit for user {user_id} to {token_limit}")
        return {"success": True, "message": f"Token limit updated to {token_limit}"}
    
    except Exception as e:
        logger.error(f"Error updating token limit: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


@router.post("/default-token-limit")
async def update_default_token_limit(request: Request):
    """Update the default token limit for new users."""
    try:
        data = await request.json()
        token_limit = data.get("token_limit")
        
        if not token_limit:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing token_limit in request"}
            )
        
        if not isinstance(token_limit, int) or token_limit < 1000:
            return JSONResponse(
                status_code=400,
                content={"error": "Token limit must be an integer >= 1000"}
            )
        
        # Update default token limit in database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            # Insert or update global default token limit
            await conn.execute(
                """
                INSERT INTO global_settings (setting_key, setting_value, updated_at)
                VALUES ('default_token_limit', $1, CURRENT_TIMESTAMP)
                ON CONFLICT (setting_key) DO UPDATE SET
                    setting_value = $1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                str(token_limit)
            )
        
        logger.info(f"Updated default token limit for new users to {token_limit}")
        return {"success": True, "message": f"Default token limit updated to {token_limit}"}
    
    except Exception as e:
        logger.error(f"Error updating default token limit: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {str(e)}"}
        )


@router.get("/dashboard", response_class=HTMLResponse)
async def get_users_dashboard():
    """Get a dashboard showing all users with message counts, token counts, and actions."""
    try:
        # Get database connection
        pool = await get_db_pool()
        
        # Get global default token limit
        async with pool.acquire() as conn:
            # Get default token limit
            default_limit_row = await conn.fetchrow("""
                SELECT setting_value, updated_at FROM global_settings 
                WHERE setting_key = 'default_token_limit'
            """)
            
            default_token_limit = int(default_limit_row["setting_value"]) if default_limit_row else 100000
            
            # Set the default token limit value for the UI
            default_token_limit_updated = default_limit_row["updated_at"] if default_limit_row else None
            
            # First get all users with message count and last active time
            users = await conn.fetch("""
                SELECT u.id, u.email, u.name, u.picture, u.created_at,
                       COUNT(m.id) as message_count,
                       MAX(m.timestamp) as last_active
                FROM users u
                LEFT JOIN messages m ON u.email = m.user_id
                GROUP BY u.id, u.email, u.name, u.picture, u.created_at
                ORDER BY u.created_at DESC
            """)
            
            # Format the results
            users_data = []
            
            # For each user, get their messages to calculate token counts
            for user in users:
                user_id = user["email"]
                
                # Get all messages for this user
                messages = await conn.fetch("""
                    SELECT content FROM messages WHERE user_id = $1
                """, user_id)
                
                # Calculate token count
                token_count = 0
                for msg in messages:
                    token_count += estimate_tokens(msg["content"])
                
                # Get user-specific token limit if it exists
                user_limit_row = await conn.fetchrow("""
                    SELECT setting_value FROM user_settings 
                    WHERE user_id = $1 AND setting_key = 'token_limit'
                """, user_id)
                
                token_limit = int(user_limit_row["setting_value"]) if user_limit_row else default_token_limit
                
                # Get user status
                status_row = await conn.fetchrow("""
                    SELECT status FROM user_status WHERE user_id = $1
                """, user_id)
                
                status = status_row["status"] if status_row else "active"
                
                # Format the last active time as a relative time string
                last_active_relative = format_relative_time(user["last_active"]) if user["last_active"] else 'Never'
                
                users_data.append({
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "picture": user["picture"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                    "last_active": user["last_active"].isoformat() if user["last_active"] else None,
                    "last_active_relative": last_active_relative,
                    "message_count": user["message_count"],
                    "token_count": token_count,
                    "token_limit": token_limit,
                    "token_percentage": min(round((token_count / token_limit) * 100), 100) if token_limit > 0 else 0,
                    "status": status
                })
            
            logger.info(f"Retrieved {len(users_data)} users for dashboard")
        
        # Generate HTML response
        html_content = generate_users_html(users_data, default_token_limit)
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"Error fetching users dashboard: {str(e)}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


def generate_users_html(users: List[Dict[str, Any]], default_token_limit: int = 100000) -> str:
    """Generate HTML for the users dashboard using Jinja2 template."""
    # Set up Jinja2 environment
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template('users/dashboard.html')
    
    # Render the template with the provided data
    html = template.render(
        users=users,
        default_token_limit=default_token_limit
    )
    
    return html
