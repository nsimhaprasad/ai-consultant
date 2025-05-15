"""User management routes."""
import logging
import os
import re
from typing import Dict, List, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse

from baid_server.api.dependencies import get_current_user
from baid_server.db.repositories.user_repository import UserRepository
from baid_server.db.repositories.message_repository import MessageRepository
from baid_server.db.database import get_db_pool


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

logger = logging.getLogger(__name__)

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


@router.get("/", response_class=HTMLResponse)
async def get_users_dashboard():
    """Get a dashboard showing all users with message counts, token counts, and actions."""
    try:
        # Get database connection
        pool = await get_db_pool()
        
        # Get global default token limit
        async with pool.acquire() as conn:
            # Get default token limit
            default_limit_row = await conn.fetchrow("""
                SELECT setting_value FROM global_settings 
                WHERE setting_key = 'default_token_limit'
            """)
            
            default_token_limit = int(default_limit_row["setting_value"]) if default_limit_row else 100000
            
            # First get all users
            users = await conn.fetch("""
                SELECT u.id, u.email, u.name, u.picture, u.created_at,
                       COUNT(m.id) as message_count
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
                
                users_data.append({
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "picture": user["picture"],
                    "created_at": user["created_at"].isoformat() if user["created_at"] else None,
                    "message_count": user["message_count"],
                    "token_count": token_count,
                    "token_limit": token_limit,
                    "token_percentage": min(round((token_count / token_limit) * 100), 100) if token_limit > 0 else 0,
                    "status": status
                })
            
            logger.info(f"Retrieved {len(users_data)} users for dashboard")
        
        # Generate HTML response
        html_content = generate_users_html(users_data)
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logger.error(f"Error fetching users dashboard: {str(e)}")
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


def generate_users_html(users: List[Dict[str, Any]]) -> str:
    """Generate HTML for the users dashboard."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>User Management Dashboard</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }
            h1 {
                color: #2c3e50;
                margin-bottom: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .card {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 20px;
                margin-bottom: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-weight: 600;
            }
            tr:hover {
                background-color: #f1f1f1;
            }
            .user-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                object-fit: cover;
            }
            .action-btn {
                display: inline-block;
                padding: 6px 12px;
                margin-right: 5px;
                background-color: #3498db;
                color: white;
                border-radius: 4px;
                text-decoration: none;
                font-size: 14px;
                cursor: pointer;
            }
            .action-btn.delete {
                background-color: #e74c3c;
            }
            .action-btn.view {
                background-color: #2ecc71;
            }
            .badge {
                display: inline-block;
                padding: 3px 8px;
                background-color: #3498db;
                color: white;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }
            .token-badge {
                background-color: #9b59b6;
            }
            .progress-container {
                width: 100%;
                background-color: #e0e0e0;
                border-radius: 4px;
                height: 8px;
                margin-top: 5px;
            }
            .progress-bar {
                height: 100%;
                border-radius: 4px;
                background-color: #3498db;
            }
            .progress-bar.warning {
                background-color: #f39c12;
            }
            .progress-bar.danger {
                background-color: #e74c3c;
            }
            .status-badge {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }
            .status-active {
                background-color: #2ecc71;
                color: white;
            }
            .status-restricted {
                background-color: #e74c3c;
                color: white;
            }
            .token-limit-input {
                width: 100px;
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            .save-btn {
                background-color: #2ecc71;
                border: none;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                margin-left: 5px;
            }
            .bulk-actions {
                padding: 15px;
                margin-bottom: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            .bulk-actions h3 {
                margin-top: 0;
                margin-bottom: 15px;
                color: #2c3e50;
            }
            .action-group {
                display: flex;
                align-items: center;
                margin-bottom: 10px;
            }
            .action-group label {
                margin-right: 10px;
                font-weight: bold;
            }
            .action-group .action-btn {
                margin-right: 10px;
            }
            
            /* Custom notification styles */
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
                max-width: 350px;
            }
            .notification {
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin-bottom: 10px;
                overflow: hidden;
                animation: slide-in 0.3s ease-out forwards;
                transform: translateX(100%);
            }
            .notification-header {
                padding: 12px 15px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                color: white;
                font-weight: bold;
            }
            .notification-success .notification-header {
                background-color: #2ecc71;
            }
            .notification-error .notification-header {
                background-color: #e74c3c;
            }
            .notification-warning .notification-header {
                background-color: #f39c12;
            }
            .notification-info .notification-header {
                background-color: #3498db;
            }
            .notification-close {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
            }
            .notification-body {
                padding: 15px;
                color: #333;
            }
            .notification-progress {
                height: 4px;
                background-color: rgba(255,255,255,0.5);
                width: 100%;
            }
            .notification-progress-bar {
                height: 100%;
                width: 100%;
                background-color: rgba(255,255,255,0.8);
                animation: progress 5s linear forwards;
            }
            @keyframes slide-in {
                to { transform: translateX(0); }
            }
            @keyframes progress {
                to { width: 0%; }
            }
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1000;
                opacity: 0;
                visibility: hidden;
                transition: opacity 0.3s ease;
            }
            .modal-overlay.active {
                opacity: 1;
                visibility: visible;
            }
            .modal {
                background-color: white;
                border-radius: 8px;
                width: 400px;
                max-width: 90%;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                transform: translateY(-20px);
                transition: transform 0.3s ease;
            }
            .modal-overlay.active .modal {
                transform: translateY(0);
            }
            .modal-header {
                padding: 15px 20px;
                border-bottom: 1px solid #eee;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .modal-title {
                font-size: 18px;
                font-weight: bold;
                margin: 0;
            }
            .modal-close {
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                color: #777;
            }
            .modal-body {
                padding: 20px;
            }
            .modal-footer {
                padding: 15px 20px;
                border-top: 1px solid #eee;
                display: flex;
                justify-content: flex-end;
            }
            .modal-btn {
                padding: 8px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                margin-left: 10px;
            }
            .modal-btn-primary {
                background-color: #3498db;
                color: white;
                border: none;
            }
            .modal-btn-danger {
                background-color: #e74c3c;
                color: white;
                border: none;
            }
            .modal-btn-cancel {
                background-color: #f1f1f1;
                color: #333;
                border: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <!-- Notification container -->
        <div class="notification-container" id="notification-container"></div>
        
        <!-- Confirmation modal -->
        <div class="modal-overlay" id="confirm-modal">
            <div class="modal">
                <div class="modal-header">
                    <h3 class="modal-title" id="modal-title">Confirm Action</h3>
                    <button class="modal-close" onclick="closeModal('confirm-modal')">&times;</button>
                </div>
                <div class="modal-body" id="modal-body">
                    Are you sure you want to proceed with this action?
                </div>
                <div class="modal-footer">
                    <button class="modal-btn modal-btn-cancel" onclick="closeModal('confirm-modal')">Cancel</button>
                    <button class="modal-btn modal-btn-primary" id="modal-confirm">Confirm</button>
                </div>
            </div>
        </div>
        
        <div class="container">
            <h1>User Management Dashboard</h1>
            <div class="card">
                <div class="bulk-actions">
                    <h3>Bulk Actions</h3>
                    <div class="action-group">
                        <label for="bulk-token-limit">Set Token Limit:</label>
                        <input type="number" id="bulk-token-limit" min="1000" step="1000" value="100000" class="token-limit-input">
                        <button class="action-btn" onclick="applyBulkTokenLimit()">Apply to Selected</button>
                    </div>
                    <div class="action-group">
                        <button class="action-btn" onclick="bulkActivateUsers()">Activate Selected</button>
                        <button class="action-btn delete" onclick="bulkRestrictUsers()">Restrict Selected</button>
                    </div>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th><input type="checkbox" id="select-all" title="Select All"></th>
                            <th>Avatar</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Created</th>
                            <th>Status</th>
                            <th>Messages</th>
                            <th>Tokens / Limit</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    """
        # Add rows for each user
    for user in users:
        avatar_img = f"<img src='{user['picture']}' class='user-avatar' alt='{user['name']}'>" if user['picture'] else "<div class='user-avatar'>👤</div>"
        created_date = user['created_at'].split('T')[0] if user['created_at'] else "N/A"
        
        # Determine progress bar color based on token usage percentage
        progress_class = ""
        if user['token_percentage'] > 90:
            progress_class = "danger"
        elif user['token_percentage'] > 70:
            progress_class = "warning"
        
        # Determine status badge class
        status_class = "status-active" if user['status'].lower() == "active" else "status-restricted"
        
        # Determine action button based on current status
        status_action = "Restrict" if user['status'].lower() == "active" else "Activate"
        status_action_class = "delete" if user['status'].lower() == "active" else "view"
        
        html += f"""
                        <tr>
                            <td><input type="checkbox" class="user-checkbox" data-user-id="{user['email']}"></td>
                            <td>{avatar_img}</td>
                            <td>{user['name']}</td>
                            <td>{user['email']}</td>
                            <td>{created_date}</td>
                            <td><span class="status-badge {status_class}">{user['status'].capitalize()}</span></td>
                            <td><span class="badge">{user['message_count']}</span></td>
                            <td>
                                <span class="badge token-badge">{user['token_count']} / {user['token_limit']}</span>
                                <div class="progress-container">
                                    <div class="progress-bar {progress_class}" style="width: {user['token_percentage']}%"></div>
                                </div>
                                <div style="margin-top: 5px;">
                                    <input type="number" class="token-limit-input" value="{user['token_limit']}" 
                                           data-user-id="{user['email']}" min="1000" step="1000">
                                    <button class="save-btn" onclick="saveTokenLimit('{user['email']}')">Save</button>
                                </div>
                            </td>
                            <td>
                                <button class="action-btn {status_action_class}" onclick="toggleUserStatus('{user['email']}', '{user['status']}')">
                                    {status_action}
                                </button>
                            </td>
                        </tr>
        """
    
    # Close the HTML
    html += """
                    </tbody>
                </table>
            </div>
        </div>
        <script>
            // Add event listeners and functions for user management
            document.addEventListener('DOMContentLoaded', function() {
                // Set up select all checkbox functionality
                const selectAllCheckbox = document.getElementById('select-all');
                const userCheckboxes = document.querySelectorAll('.user-checkbox');
                
                selectAllCheckbox.addEventListener('change', function() {
                    userCheckboxes.forEach(checkbox => {
                        checkbox.checked = selectAllCheckbox.checked;
                    });
                });
                
                // Update select all checkbox when individual checkboxes change
                userCheckboxes.forEach(checkbox => {
                    checkbox.addEventListener('change', function() {
                        const allChecked = Array.from(userCheckboxes).every(cb => cb.checked);
                        const someChecked = Array.from(userCheckboxes).some(cb => cb.checked);
                        
                        selectAllCheckbox.checked = allChecked;
                        selectAllCheckbox.indeterminate = someChecked && !allChecked;
                    });
                });
            });
            
            // Custom notification functions
            function showNotification(message, type = 'info', duration = 5000) {
                const container = document.getElementById('notification-container');
                const notification = document.createElement('div');
                notification.className = `notification notification-${type}`;
                
                // Create notification content
                notification.innerHTML = `
                    <div class="notification-header">
                        <span>${type.charAt(0).toUpperCase() + type.slice(1)}</span>
                        <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
                    </div>
                    <div class="notification-body">${message}</div>
                    <div class="notification-progress">
                        <div class="notification-progress-bar"></div>
                    </div>
                `;
                
                // Add to container
                container.appendChild(notification);
                
                // Auto-remove after duration
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, duration);
                
                return notification;
            }
            
            // Show confirmation dialog
            function showConfirmDialog(title, message, confirmCallback, confirmButtonText = 'Confirm', confirmButtonClass = 'modal-btn-primary') {
                const modal = document.getElementById('confirm-modal');
                const modalTitle = document.getElementById('modal-title');
                const modalBody = document.getElementById('modal-body');
                const confirmButton = document.getElementById('modal-confirm');
                
                // Set content
                modalTitle.textContent = title;
                modalBody.textContent = message;
                confirmButton.textContent = confirmButtonText;
                confirmButton.className = `modal-btn ${confirmButtonClass}`;
                
                // Set confirm action
                confirmButton.onclick = () => {
                    closeModal('confirm-modal');
                    confirmCallback();
                };
                
                // Show modal
                modal.classList.add('active');
            }
            
            // Close modal
            function closeModal(modalId) {
                const modal = document.getElementById(modalId);
                modal.classList.remove('active');
            }
            
            // Function to toggle user status (active/restricted)
            async function toggleUserStatus(userId, currentStatus) {
                const newStatus = currentStatus.toLowerCase() === 'active' ? 'restricted' : 'active';
                const action = newStatus === 'active' ? 'activate' : 'restrict';
                const buttonClass = newStatus === 'active' ? 'modal-btn-primary' : 'modal-btn-danger';
                
                showConfirmDialog(
                    `${action.charAt(0).toUpperCase() + action.slice(1)} User`,
                    `Are you sure you want to ${action} user ${userId}?`,
                    async () => {
                        try {
                            const response = await fetch('/users/status', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    user_id: userId,
                                    status: newStatus
                                })
                            });
                            
                            if (response.ok) {
                                showNotification(`User ${userId} has been ${action}d successfully.`, 'success');
                                // Reload the page to reflect changes
                                setTimeout(() => window.location.reload(), 1500);
                            } else {
                                showNotification(`Failed to ${action} user. Please try again.`, 'error');
                            }
                        } catch (error) {
                            showNotification(`Error: ${error.message}`, 'error');
                        }
                    },
                    action.charAt(0).toUpperCase() + action.slice(1),
                    buttonClass
                );
            }
            
            // Function to get selected user IDs
            function getSelectedUserIds() {
                const checkboxes = document.querySelectorAll('.user-checkbox:checked');
                return Array.from(checkboxes).map(checkbox => checkbox.dataset.userId);
            }
            
            // Function to apply bulk token limit
            async function applyBulkTokenLimit() {
                const userIds = getSelectedUserIds();
                if (userIds.length === 0) {
                    showNotification('Please select at least one user.', 'warning');
                    return;
                }
                
                const tokenLimit = parseInt(document.getElementById('bulk-token-limit').value);
                if (!tokenLimit || isNaN(tokenLimit) || tokenLimit < 1000) {
                    showNotification('Please enter a valid token limit (minimum 1000)', 'warning');
                    return;
                }
                
                showConfirmDialog(
                    'Set Token Limit',
                    `Apply token limit of ${tokenLimit} to ${userIds.length} selected users?`,
                    async () => {
                        try {
                            const promises = userIds.map(userId => 
                                fetch('/users/token-limit', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({
                                        user_id: userId,
                                        token_limit: tokenLimit
                                    })
                                })
                            );
                            
                            const results = await Promise.all(promises);
                            const allSuccessful = results.every(response => response.ok);
                            
                            if (allSuccessful) {
                                showNotification(`Token limit updated for ${userIds.length} users.`, 'success');
                                setTimeout(() => window.location.reload(), 1500);
                            } else {
                                showNotification('Some updates failed. Please check and try again.', 'error');
                            }
                        } catch (error) {
                            showNotification(`Error: ${error.message}`, 'error');
                        }
                    }
                );
            }
            
            // Function to bulk activate users
            async function bulkActivateUsers() {
                await bulkUpdateStatus('active');
            }
            
            // Function to bulk restrict users
            async function bulkRestrictUsers() {
                await bulkUpdateStatus('restricted');
            }
            
            // Function to update status for multiple users
            async function bulkUpdateStatus(status) {
                const userIds = getSelectedUserIds();
                if (userIds.length === 0) {
                    showNotification('Please select at least one user.', 'warning');
                    return;
                }
                
                const action = status === 'active' ? 'activate' : 'restrict';
                const buttonClass = status === 'active' ? 'modal-btn-primary' : 'modal-btn-danger';
                
                showConfirmDialog(
                    `${action.charAt(0).toUpperCase() + action.slice(1)} Users`,
                    `Are you sure you want to ${action} ${userIds.length} selected users?`,
                    async () => {
                        try {
                            const promises = userIds.map(userId => 
                                fetch('/users/status', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({
                                        user_id: userId,
                                        status: status
                                    })
                                })
                            );
                            
                            const results = await Promise.all(promises);
                            const allSuccessful = results.every(response => response.ok);
                            
                            if (allSuccessful) {
                                showNotification(`${userIds.length} users have been ${action}d successfully.`, 'success');
                                setTimeout(() => window.location.reload(), 1500);
                            } else {
                                showNotification(`Some users could not be ${action}d. Please check and try again.`, 'error');
                            }
                        } catch (error) {
                            showNotification(`Error: ${error.message}`, 'error');
                        }
                    },
                    action.charAt(0).toUpperCase() + action.slice(1),
                    buttonClass
                );
            }
            
            // Function to save token limit
            async function saveTokenLimit(userId) {
                const input = document.querySelector(`input[data-user-id="${userId}"]`);
                const newLimit = input.value;
                
                if (!newLimit || isNaN(newLimit) || newLimit < 1000) {
                    showNotification('Please enter a valid token limit (minimum 1000)', 'warning');
                    return;
                }
                
                try {
                    const response = await fetch('/users/token-limit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            user_id: userId,
                            token_limit: parseInt(newLimit)
                        })
                    });
                    
                    if (response.ok) {
                        showNotification(`Token limit for ${userId} has been updated to ${newLimit}.`, 'success');
                        // Reload the page to reflect changes
                        setTimeout(() => window.location.reload(), 1500);
                    } else {
                        showNotification('Failed to update token limit. Please try again.', 'error');
                    }
                } catch (error) {
                    showNotification(`Error: ${error.message}`, 'error');
                }
            }
        </script>
    </body>
    </html>
    """
    
    return html
