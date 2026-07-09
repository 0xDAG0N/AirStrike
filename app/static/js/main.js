/**
 * Main JavaScript for AirStrike Web Interface
 * 
 * This is the entry point for the application that initializes the appropriate
 * modules based on the current page.
 */

// Import page modules
import { initDashboard } from './modules/pages/dashboard.js';
import { initScanPage } from './modules/pages/scan.js';
import { initAttackPage } from './modules/pages/attack.js';
import { initResultsPage } from './modules/pages/results.js';
import { initSettingsPage } from './modules/pages/settings.js';

// Import state management
import { loadSavedState } from './modules/state.js';

// Import notifications
import { success, info, warning, error } from './modules/notifications.js';

// Debug mode - set to true to enable console logging
const DEBUG = true;

// Simple debug utility
function debug(area, message, data = null) {
    if (!DEBUG) return;
    console.log(`[${area}] ${message}`, data || '');
}

// DOM Ready function
document.addEventListener('DOMContentLoaded', function() {
    debug('PAGE', 'DOM Content Loaded');
    
    try {
        // Monitor loading overlay for debugging
        monitorLoadingOverlay();
        
        // Load any saved state from session storage
        loadSavedState();
        
        // Initialize the appropriate page module based on the current page
        initializePage();
        
        // Convert flash messages to notifications
        convertFlashMessages();
        
        // Welcome notification
        const currentPage = getCurrentPage();
        if (currentPage === 'dashboard') {
            setTimeout(() => {
                info('Welcome to AirStrike', 'System Ready', { duration: 7000 });
            }, 1500);
        }
    } catch (error) {
        console.error('Error initializing application:', error);
        error('Failed to initialize application. Check console for details.');
    }
});

window.addEventListener('load', function() {
    debug('PAGE', 'Window Load Complete');
});

/**
 * Initialize the appropriate page module based on the current page
 */
function initializePage() {
    // Determine current page based on URL or page elements
    const currentPage = getCurrentPage();
    
    // Initialize the appropriate page module
    try {
    switch (currentPage) {
        case 'dashboard':
            initDashboard();
            break;
        case 'scan':
            initScanPage();
                success('Scan module initialized', 'Ready');
            break;
        case 'attack':
            initAttackPage();
                warning('Attack module active', 'Caution', { 
                    duration: 8000,
                    dismissible: true
                });
            break;
        case 'results':
            initResultsPage();
                info('Results loaded', 'Data Ready');
            break;
        case 'settings':
            initSettingsPage();
                info('Settings page loaded', 'Configuration');
            break;
        default:
            console.log('Unknown page or no specific initialization needed');
    }
    } catch (error) {
        console.error(`Error initializing ${currentPage} page:`, error);
        error(`Failed to initialize ${currentPage} page`, 'Error');
    }
}

/**
 * Convert Flask flash messages to our notification system
 */
function convertFlashMessages() {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    // Get all alert elements
    const alerts = alertsContainer.querySelectorAll('.alert');
    
    // Convert each alert to a notification
    alerts.forEach((alert, index) => {
        // Determine the alert type
        let type = 'info';
        if (alert.classList.contains('alert-danger')) {
            type = 'error';
        } else if (alert.classList.contains('alert-warning')) {
            type = 'warning';
        } else if (alert.classList.contains('alert-success')) {
            type = 'success';
        }
        
        // Get the message
        const message = alert.textContent.trim();
        
        // Show notification with a slight delay between each
        setTimeout(() => {
            // Use our notification system
            switch (type) {
                case 'success':
                    success(message);
                    break;
                case 'error':
                    error(message);
                    break;
                case 'warning':
                    warning(message);
                    break;
                default:
                    info(message);
            }
        }, index * 300);
        
        // Hide the original alert
        alert.style.display = 'none';
    });
}

/**
 * Determine the current page based on URL or page elements
 * @returns {string} The current page identifier
 */
function getCurrentPage() {
    // Check URL path
    const path = window.location.pathname;
    
    if (path === '/' || path === '/index') {
        return 'dashboard';
    } else if (path === '/scan') {
        return 'scan';
    } else if (path === '/attack') {
        return 'attack';
    } else if (path === '/results') {
        return 'results';
    } else if (path === '/settings') {
        return 'settings';
    }
    
    // Fallback to checking page elements
    if (document.getElementById('dashboard-stats')) {
        return 'dashboard';
    } else if (document.getElementById('scan-networks-btn')) {
        return 'scan';
    } else if (document.getElementById('attack-options')) {
        return 'attack';
    } else if (document.getElementById('attack-log')) {
        return 'results';
    } else if (document.getElementById('interface-select')) {
        return 'settings';
    }
    
    // Default
    return 'unknown';
}

// Export notification functions for use in other modules
export { success, info, warning, error };

// Monitor the loading overlay
function monitorLoadingOverlay() {
    // Monitor loading overlay visibility
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        debug('OVERLAY', 'Monitoring loading overlay visibility');
        
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'style' || 
                    mutation.attributeName === 'class') {
                    const isVisible = 
                        loadingOverlay.style.visibility !== 'hidden' && 
                        !loadingOverlay.classList.contains('hidden');
                    debug('OVERLAY', 'Loading overlay visibility changed', isVisible);
                }
            });
        });
        
        observer.observe(loadingOverlay, { 
            attributes: true,
            attributeFilter: ['style', 'class']
        });
    } else {
        debug('OVERLAY', 'Loading overlay element not found');
    }
}

// Initialize common UI components
function initializeUI() {
    // Set up alerts
    setupAlerts();
    
    // Set up theme toggle
    setupThemeToggle();
}

// Set up alert dismissal
function setupAlerts() {
    document.querySelectorAll('.alert').forEach(function(alert) {
        if (!alert.querySelector('.close-btn')) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'close-btn';
            closeBtn.innerHTML = '&times;';
            closeBtn.addEventListener('click', function() {
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.style.display = 'none';
                }, 300);
            });
            alert.appendChild(closeBtn);
        }
    });
}

// Set up theme toggle
function setupThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    // Set initial state based on saved theme
    const currentTheme = document.documentElement.getAttribute('data-theme');
    themeToggle.checked = currentTheme === 'light';
    
    // Listen for changes
    themeToggle.addEventListener('change', function() {
        const newTheme = this.checked ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        debug('THEME', 'Theme changed to', newTheme);
    });
}

// Show an alert message
window.showAlert = function(message, type = 'info') {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = message;
    
    const closeBtn = document.createElement('button');
    closeBtn.className = 'close-btn';
    closeBtn.innerHTML = '&times;';
    closeBtn.addEventListener('click', function() {
        alert.style.opacity = '0';
        setTimeout(function() {
            alert.remove();
        }, 300);
    });
    
    alert.appendChild(closeBtn);
    alertsContainer.appendChild(alert);
    
    // Auto-hide after 5 seconds for non-error alerts
    if (type !== 'danger' && type !== 'error') {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    }
};
