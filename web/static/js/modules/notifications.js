/**
 * Notifications Module for AirStrike
 * Provides a modern notification system for alerts and messages
 */

// Create notification container if it doesn't exist
function createNotificationContainer() {
    if (!document.querySelector('.notification-container')) {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
}

/**
 * Show a notification
 * @param {Object} options - Notification options
 * @param {string} options.title - Notification title
 * @param {string} options.message - Notification message
 * @param {string} options.type - Notification type (success, error, warning, info)
 * @param {number} options.duration - Duration in ms (default: 5000)
 * @param {boolean} options.dismissible - Whether the notification can be dismissed (default: true)
 * @returns {HTMLElement} The notification element
 */
export function showNotification(options) {
    // Default options
    const defaults = {
        title: 'Notification',
        message: '',
        type: 'info', // success, error, warning, info
        duration: 5000,
        dismissible: true
    };
    
    // Merge defaults with options
    const settings = { ...defaults, ...options };
    
    // Create container if it doesn't exist
    createNotificationContainer();
    const container = document.querySelector('.notification-container');
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${settings.type}`;
    
    // Set icon based on type
    let icon = '';
    switch (settings.type) {
        case 'success':
            icon = '✓';
            break;
        case 'error':
            icon = '✕';
            break;
        case 'warning':
            icon = '⚠';
            break;
        case 'info':
        default:
            icon = 'ℹ';
            break;
    }
    
    // Build notification HTML
    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-content">
            <div class="notification-title">${settings.title}</div>
            <p class="notification-message">${settings.message}</p>
        </div>
        ${settings.dismissible ? '<button class="notification-close">×</button>' : ''}
        <div class="notification-progress"></div>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Force reflow to ensure animation works
    void notification.offsetWidth;
    
    // Show notification
    notification.classList.add('show');
    
    // Set progress animation duration
    const progressBar = notification.querySelector('.notification-progress');
    if (progressBar) {
        progressBar.style.animationDuration = `${settings.duration}ms`;
    }
    
    // Handle close button
    if (settings.dismissible) {
        const closeButton = notification.querySelector('.notification-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                closeNotification(notification);
            });
        }
    }
    
    // Auto dismiss after duration
    if (settings.duration > 0) {
        setTimeout(() => {
            closeNotification(notification);
        }, settings.duration);
    }
    
    return notification;
}

/**
 * Close a notification
 * @param {HTMLElement} notification - The notification element to close
 */
function closeNotification(notification) {
    // Add hide class
    notification.classList.add('hide');
    notification.classList.remove('show');
    
    // Remove after animation completes
    setTimeout(() => {
        if (notification.parentElement) {
            notification.parentElement.removeChild(notification);
        }
    }, 300); // Match transition duration
}

/**
 * Success notification shorthand
 * @param {string} message - The notification message
 * @param {string} title - The notification title (optional)
 * @param {Object} options - Additional options (optional)
 */
export function success(message, title = 'Success', options = {}) {
    return showNotification({
        title,
        message,
        type: 'success',
        ...options
    });
}

/**
 * Error notification shorthand
 * @param {string} message - The notification message
 * @param {string} title - The notification title (optional)
 * @param {Object} options - Additional options (optional)
 */
export function error(message, title = 'Error', options = {}) {
    return showNotification({
        title,
        message,
        type: 'error',
        ...options
    });
}

/**
 * Warning notification shorthand
 * @param {string} message - The notification message
 * @param {string} title - The notification title (optional)
 * @param {Object} options - Additional options (optional)
 */
export function warning(message, title = 'Warning', options = {}) {
    return showNotification({
        title,
        message,
        type: 'warning',
        ...options
    });
}

/**
 * Info notification shorthand
 * @param {string} message - The notification message
 * @param {string} title - The notification title (optional)
 * @param {Object} options - Additional options (optional)
 */
export function info(message, title = 'Information', options = {}) {
    return showNotification({
        title,
        message,
        type: 'info',
        ...options
    });
}

// Initialize the module
document.addEventListener('DOMContentLoaded', () => {
    createNotificationContainer();
}); 