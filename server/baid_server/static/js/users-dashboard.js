/**
 * Users Dashboard JavaScript
 * Contains all the functionality for the user management dashboard
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize select all checkbox functionality
    initializeSelectAllCheckbox();
    
    // Initialize formatted number inputs
    initializeFormattedNumberInputs();
});

/**
 * Initialize formatted number inputs with comma separators
 */
function initializeFormattedNumberInputs() {
    // Format the default token limit input
    const defaultTokenInput = document.getElementById('default-token-limit');
    if (defaultTokenInput) {
        // Create a formatted display next to the input
        const formattedDisplay = document.createElement('span');
        formattedDisplay.className = 'formatted-number';
        formattedDisplay.textContent = Number(defaultTokenInput.value).toLocaleString();
        defaultTokenInput.parentNode.insertBefore(formattedDisplay, defaultTokenInput.nextSibling);
        defaultTokenInput.style.display = 'none';
        
        // Update the hidden input when clicking on the formatted display
        formattedDisplay.addEventListener('click', function() {
            formattedDisplay.style.display = 'none';
            defaultTokenInput.style.display = 'inline-block';
            defaultTokenInput.focus();
        });
        
        // Update the formatted display when the input loses focus
        defaultTokenInput.addEventListener('blur', function() {
            formattedDisplay.textContent = Number(defaultTokenInput.value).toLocaleString();
            defaultTokenInput.style.display = 'none';
            formattedDisplay.style.display = 'inline-block';
        });
    }
    
    // Format all user token limit inputs
    const tokenInputs = document.querySelectorAll('input.token-input[data-user-id]');
    tokenInputs.forEach(input => {
        // Create a formatted display for each input
        const formattedDisplay = document.createElement('span');
        formattedDisplay.className = 'formatted-number';
        formattedDisplay.textContent = Number(input.value).toLocaleString();
        input.parentNode.insertBefore(formattedDisplay, input.nextSibling);
        input.style.display = 'none';
        
        // Update the hidden input when clicking on the formatted display
        formattedDisplay.addEventListener('click', function() {
            formattedDisplay.style.display = 'none';
            input.style.display = 'inline-block';
            input.focus();
        });
        
        // Update the formatted display when the input loses focus
        input.addEventListener('blur', function() {
            formattedDisplay.textContent = Number(input.value).toLocaleString();
            input.style.display = 'none';
            formattedDisplay.style.display = 'inline-block';
        });
    });
}

/**
 * Initialize the select all checkbox functionality
 */
function initializeSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all-checkbox');
    const userCheckboxes = document.querySelectorAll('.user-checkbox');
    
    // Update individual checkboxes when select all changes
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
}

/**
 * Show a notification message
 * @param {string} message - The message to display
 * @param {string} type - The type of notification (info, success, error, warning)
 * @param {number} duration - How long to show the notification in milliseconds
 * @returns {HTMLElement} - The notification element
 */
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

/**
 * Show a confirmation dialog
 * @param {string} title - The title of the dialog
 * @param {string} message - The message to display
 * @param {Function} confirmCallback - Function to call when confirmed
 * @param {string} confirmButtonText - Text for the confirm button
 * @param {string} confirmButtonClass - CSS class for the confirm button
 */
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

/**
 * Close a modal dialog
 * @param {string} modalId - The ID of the modal to close
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('active');
}

/**
 * Toggle a user's status between active and restricted
 * @param {string} userId - The user ID to toggle
 * @param {string} currentStatus - The current status of the user
 */
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

/**
 * Get selected user IDs from checkboxes
 * @returns {Array} - Array of selected user IDs
 */
function getSelectedUserIds() {
    const checkboxes = document.querySelectorAll('.user-checkbox:checked');
    return Array.from(checkboxes).map(checkbox => checkbox.dataset.userId);
}

/**
 * Apply a token limit to multiple selected users
 */
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

/**
 * Bulk activate multiple users
 */
async function bulkActivateUsers() {
    await bulkUpdateStatus('active');
}

/**
 * Bulk restrict multiple users
 */
async function bulkRestrictUsers() {
    await bulkUpdateStatus('restricted');
}

/**
 * Update status for multiple users
 * @param {string} status - The status to set ('active' or 'restricted')
 */
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

/**
 * Save the default token limit for new users
 */
async function saveDefaultTokenLimit() {
    const defaultLimit = parseInt(document.getElementById('default-token-limit').value);
    
    if (!defaultLimit || isNaN(defaultLimit) || defaultLimit < 1000) {
        showNotification('Please enter a valid token limit (minimum 1000)', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/users/default-token-limit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                token_limit: defaultLimit
            })
        });
        
        if (response.ok) {
            showNotification(`Default token limit for new users has been updated to ${defaultLimit.toLocaleString()}.`, 'success');
            // Reload the page to reflect changes
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showNotification('Failed to update default token limit. Please try again.', 'error');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

/**
 * Save token limit for a specific user
 * @param {string} userId - The user ID to update
 */
async function saveTokenLimit(userId) {
    // Use a more specific selector to target only the token input, not the checkbox
    const input = document.querySelector(`input.token-input[data-user-id="${userId}"]`);
    const newLimit = input.value.trim();
    const newLimitInt = parseInt(newLimit, 10);
    
    // Check if the input is valid
    if (newLimit === '' || isNaN(newLimitInt)) {
        showNotification('Please enter a valid token limit', 'warning');
        return;
    }
    
    // Check if the input meets the minimum requirement
    if (newLimitInt < 1000) {
        showNotification('Token limit must be at least 1000', 'warning');
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
                token_limit: newLimitInt
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
